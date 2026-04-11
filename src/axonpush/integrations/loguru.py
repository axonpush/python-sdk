"""Loguru integration for AxonPush.

Loguru is a popular alternative to stdlib ``logging`` that's loved for its
ergonomic API. This integration provides a sink function that can be added
to a Loguru logger to forward records to AxonPush.

Requires: ``pip install axonpush[loguru]``

Usage::

    from loguru import logger
    from axonpush import AxonPush
    from axonpush.integrations.loguru import create_axonpush_loguru_sink

    client = AxonPush(api_key="ak_...", tenant_id="1")
    sink = create_axonpush_loguru_sink(
        client=client,
        channel_id=1,
        service_name="my-api",
    )
    logger.add(sink, serialize=True)

    logger.error("connection refused", user_id=42)
"""
from __future__ import annotations

import json
import logging as _stdlib_logging
from typing import Any, Dict, Literal, Optional, TYPE_CHECKING

try:
    import loguru  # noqa: F401 — verify the package is installed
except ImportError:
    raise ImportError(
        "Loguru integration requires the 'loguru' extra. "
        "Install it with: pip install axonpush[loguru]"
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

__all__ = ["create_axonpush_loguru_sink", "flush_after_invocation"]

_internal_logger = _stdlib_logging.getLogger("axonpush")


class _AxonPushLoguruSink:
    """Callable sink that forwards Loguru records to AxonPush.

    Instances are drop-in replacements for a plain sink function — the
    object has a ``__call__`` method so ``logger.add(sink, serialize=True)``
    keeps working. Adds ``flush(timeout=)`` and ``close()`` methods for
    graceful shutdown / Lambda-invocation flushing.
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
                "AxonPush detected %s. Call sink.flush() at the end of each "
                "invocation (or wrap your handler with "
                "axonpush.integrations.loguru.flush_after_invocation) to "
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

    def __call__(self, message: Any) -> None:
        try:
            publish_kwargs = self._build_publish_kwargs(message)
        except Exception as exc:
            _internal_logger.warning("AxonPush loguru sink failed: %s", exc)
            return

        if self._publisher is not None:
            self._publisher.submit(publish_kwargs)
            return

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
            _internal_logger.warning("AxonPush loguru sink failed: %s", exc)

    def _build_publish_kwargs(self, message: Any) -> Dict[str, Any]:
        if isinstance(message, str):
            record_dict = json.loads(message).get("record", {})
        else:
            record_dict = getattr(message, "record", {}) or {}

        level_raw = record_dict.get("level")
        if isinstance(level_raw, dict):
            level_name = level_raw.get("name", "INFO")
        else:
            level_name = str(level_raw or "INFO")
        severity_number, severity_text = severity_from_text(level_name)

        body = record_dict.get("message", "")

        attributes: Dict[str, Any] = {}
        file_info = record_dict.get("file")
        if isinstance(file_info, dict):
            if "path" in file_info:
                attributes["code.filepath"] = file_info["path"]
            if "name" in file_info:
                attributes["code.filename"] = file_info["name"]
        if "function" in record_dict:
            attributes["code.function"] = record_dict["function"]
        if "line" in record_dict:
            attributes["code.lineno"] = record_dict["line"]
        if "module" in record_dict:
            attributes["code.namespace"] = record_dict["module"]
        if "name" in record_dict:
            attributes["logger.name"] = record_dict["name"]
        proc = record_dict.get("process")
        if isinstance(proc, dict) and "id" in proc:
            attributes["process.pid"] = proc["id"]
        thr = record_dict.get("thread")
        if isinstance(thr, dict) and "name" in thr:
            attributes["thread.name"] = thr["name"]

        extra = record_dict.get("extra")
        if isinstance(extra, dict):
            for key, value in extra.items():
                attributes[key] = value

        exception = record_dict.get("exception")
        if isinstance(exception, dict):
            if "type" in exception:
                attributes["exception.type"] = exception["type"]
            if "value" in exception:
                attributes["exception.message"] = exception["value"]

        time_field = record_dict.get("time")
        time_unix_nano: Optional[str] = None
        if isinstance(time_field, dict) and "timestamp" in time_field:
            ts = time_field["timestamp"]
            if isinstance(ts, (int, float)):
                time_unix_nano = str(int(ts * 1_000_000_000))

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
            "identifier": str(record_dict.get("name", "loguru")),
            "payload": payload,
            "channel_id": self._channel_id,
            "agent_id": self._agent_id,
            "trace_id": trace.trace_id,
            "span_id": trace.next_span_id(),
            "event_type": self._event_type,
            "metadata": {"framework": "loguru"},
        }


def create_axonpush_loguru_sink(
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
) -> _AxonPushLoguruSink:
    """Build a Loguru sink that forwards each record to AxonPush.

    Pass the returned object to ``logger.add(sink, serialize=True)``.
    The ``serialize=True`` flag is **required** — it tells Loguru to pass
    a JSON string of the record to the sink, which this integration parses.

    The returned object is a callable instance; it exposes ``flush()`` and
    ``close()`` methods for graceful shutdown / per-invocation flushing
    (e.g. in AWS Lambda). Publishing is non-blocking by default — records
    are enqueued and drained by a background worker thread. Pass
    ``mode="sync"`` to fall back to synchronous blocking publishes.
    """
    return _AxonPushLoguruSink(
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
