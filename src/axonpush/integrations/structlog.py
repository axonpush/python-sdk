"""Structlog integration for AxonPush.

Structlog is the Python ecosystem's go-to library for structured logging in
production services. This integration provides a structlog ``processor`` that
forwards each log event to AxonPush as an OpenTelemetry-shaped ``app.log``.

Requires: ``pip install axonpush[structlog]``

Usage::

    import structlog
    from axonpush import AxonPush
    from axonpush.integrations.structlog import axonpush_structlog_processor

    client = AxonPush(api_key="ak_...", tenant_id="1")
    forwarder = axonpush_structlog_processor(
        client=client,
        channel_id=1,
        service_name="my-api",
    )

    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            forwarder,
            structlog.processors.JSONRenderer(),
        ],
    )

    log = structlog.get_logger()
    log.error("connection refused", user_id=42)
"""
from __future__ import annotations

import logging as _stdlib_logging
import time
from typing import Any, Dict, Literal, MutableMapping, Optional, TYPE_CHECKING

try:
    import structlog  # noqa: F401 — verify the package is installed
except ImportError:
    raise ImportError(
        "Structlog integration requires the 'structlog' extra. "
        "Install it with: pip install axonpush[structlog]"
    ) from None

from axonpush._tracing import current_trace, get_or_create_trace
from axonpush.integrations._otel_payload import (
    build_log_payload,
    severity_from_text,
)
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    detect_serverless,
    flush_after_invocation,
)
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

__all__ = ["axonpush_structlog_processor", "flush_after_invocation"]

_internal_logger = _stdlib_logging.getLogger("axonpush")


class _AxonPushStructlogProcessor:
    """Callable structlog processor that forwards events to AxonPush.

    Non-destructive — returns the event dict unchanged so downstream
    processors see it intact. Exposes ``flush(timeout=)`` and ``close()``
    for graceful shutdown / Lambda-invocation flushing.
    """

    def __init__(
        self,
        *,
        client: "AxonPush | AsyncAxonPush",
        channel_id: int,
        source: str = "app",
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        environment: Optional[str] = None,
        agent_id: Optional[str] = None,
        mode: Optional[Literal["background", "sync"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
    ) -> None:
        if source not in ("agent", "app"):
            raise ValueError(f"source must be 'agent' or 'app', got {source!r}")
        resolved_mode = mode or "background"
        if resolved_mode not in ("background", "sync"):
            raise ValueError(
                f"mode must be 'background' or 'sync', got {resolved_mode!r}"
            )

        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._event_type = (
            EventType.APP_LOG if source == "app" else EventType.AGENT_LOG
        )

        resource: Dict[str, Any] = {}
        if service_name is not None:
            resource["service.name"] = service_name
        if service_version is not None:
            resource["service.version"] = service_version
        if environment is not None:
            resource["deployment.environment"] = environment
        self._resource = resource or None

        if resolved_mode == "background":
            self._publisher: Optional[BackgroundPublisher] = BackgroundPublisher(
                client,
                queue_size=queue_size,
                shutdown_timeout=shutdown_timeout,
            )
        else:
            self._publisher = None

        serverless = detect_serverless()
        if serverless is not None and self._publisher is not None:
            _internal_logger.info(
                "AxonPush detected %s. Call processor.flush() at the end of "
                "each invocation (or wrap your handler with "
                "axonpush.integrations.structlog.flush_after_invocation) to "
                "avoid losing records when the container is frozen.",
                serverless,
            )

    def flush(self, timeout: Optional[float] = None) -> None:
        """Block until queued records are published, or until timeout."""
        if self._publisher is not None:
            self._publisher.flush(timeout)

    def close(self) -> None:
        """Stop the background worker and release resources."""
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None

    def __call__(
        self,
        _logger: Any,
        method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        try:
            publish_kwargs = self._build_publish_kwargs(method_name, event_dict)
        except Exception as exc:
            _internal_logger.warning("AxonPush structlog processor failed: %s", exc)
            return event_dict

        if self._publisher is not None:
            self._publisher.submit(publish_kwargs)
            return event_dict

        try:
            result = self._client.events.publish(**publish_kwargs)
            import asyncio
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
        except Exception as exc:
            _internal_logger.warning("AxonPush structlog processor failed: %s", exc)

        return event_dict

    def _build_publish_kwargs(
        self,
        method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> Dict[str, Any]:
        level_name = str(event_dict.get("level") or method_name).upper()
        severity_number, severity_text = severity_from_text(level_name)

        body = event_dict.get("event", "")

        attributes: Dict[str, Any] = {}
        for key, value in event_dict.items():
            if key in ("event", "level", "timestamp", "time"):
                continue
            attributes[key] = value

        ts_value = event_dict.get("timestamp") or event_dict.get("time")
        if isinstance(ts_value, (int, float)):
            time_unix_nano = str(int(ts_value * 1_000_000_000))
        elif isinstance(ts_value, str):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
                time_unix_nano = str(int(dt.timestamp() * 1_000_000_000))
            except (ValueError, AttributeError):
                time_unix_nano = str(int(time.time() * 1_000_000_000))
        else:
            time_unix_nano = str(int(time.time() * 1_000_000_000))

        payload = build_log_payload(
            body=body,
            severity_number=severity_number,
            severity_text=severity_text,
            time_unix_nano=time_unix_nano,
            attributes=attributes or None,
            resource=self._resource,
        )

        trace = current_trace() or get_or_create_trace()

        return {
            "identifier": "structlog",
            "payload": payload,
            "channel_id": self._channel_id,
            "agent_id": self._agent_id,
            "trace_id": trace.trace_id,
            "span_id": trace.next_span_id(),
            "event_type": self._event_type,
            "metadata": {"framework": "structlog"},
        }


def axonpush_structlog_processor(
    *,
    client: "AxonPush | AsyncAxonPush",
    channel_id: int,
    source: str = "app",
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    environment: Optional[str] = None,
    agent_id: Optional[str] = None,
    mode: Optional[Literal["background", "sync"]] = None,
    queue_size: int = DEFAULT_QUEUE_SIZE,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
) -> _AxonPushStructlogProcessor:
    """Return a structlog processor that forwards events to AxonPush.

    The processor is non-destructive — it does NOT modify the event dict
    that flows to subsequent processors. Place it BEFORE the renderer
    (JSONRenderer / KeyValueRenderer) in the processor chain.

    The returned object is a callable instance and exposes ``flush()`` /
    ``close()`` methods for graceful shutdown. Publishing is non-blocking
    by default; pass ``mode="sync"`` to fall back to blocking publishes.
    """
    return _AxonPushStructlogProcessor(
        client=client,
        channel_id=channel_id,
        source=source,
        service_name=service_name,
        service_version=service_version,
        environment=environment,
        agent_id=agent_id,
        mode=mode,
        queue_size=queue_size,
        shutdown_timeout=shutdown_timeout,
    )
