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
from typing import Any, Callable, Dict, MutableMapping, Optional, TYPE_CHECKING

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
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = _stdlib_logging.getLogger("axonpush")


def axonpush_structlog_processor(
    *,
    client: "AxonPush | AsyncAxonPush",
    channel_id: int,
    source: str = "app",
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    environment: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Callable[[Any, str, MutableMapping[str, Any]], MutableMapping[str, Any]]:
    """Return a structlog processor that forwards events to AxonPush.

    The processor is non-destructive — it does NOT modify the event dict that
    flows to subsequent processors. It just emits a side-effect publish call.
    Place it BEFORE the renderer (JSONRenderer / KeyValueRenderer) in the
    processor chain.
    """
    if source not in ("agent", "app"):
        raise ValueError(f"source must be 'agent' or 'app', got {source!r}")

    resource: Dict[str, Any] = {}
    if service_name is not None:
        resource["service.name"] = service_name
    if service_version is not None:
        resource["service.version"] = service_version
    if environment is not None:
        resource["deployment.environment"] = environment
    resource_or_none = resource or None

    event_type = EventType.APP_LOG if source == "app" else EventType.AGENT_LOG

    def processor(
        _logger: Any,
        method_name: str,
        event_dict: MutableMapping[str, Any],
    ) -> MutableMapping[str, Any]:
        try:
            # Severity: prefer explicit "level" key, fall back to method name
            level_name = str(event_dict.get("level") or method_name).upper()
            severity_number, severity_text = severity_from_text(level_name)

            body = event_dict.get("event", "")

            # Build attributes from everything else in the event_dict
            attributes: Dict[str, Any] = {}
            for key, value in event_dict.items():
                if key in ("event", "level", "timestamp", "time"):
                    continue
                attributes[key] = value

            # timeUnixNano: structlog usually adds an ISO 'timestamp' field via
            # TimeStamper. We try to convert that, otherwise fall back to now.
            time_unix_nano: Optional[str] = None
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
                resource=resource_or_none,
            )

            trace = current_trace() or get_or_create_trace()

            result = client.events.publish(
                identifier="structlog",
                payload=payload,
                channel_id=channel_id,
                agent_id=agent_id,
                trace_id=trace.trace_id,
                span_id=trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "structlog"},
            )

            import asyncio

            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
        except Exception as exc:
            _internal_logger.warning("AxonPush structlog processor failed: %s", exc)

        # Pass through the event dict unchanged
        return event_dict

    return processor
