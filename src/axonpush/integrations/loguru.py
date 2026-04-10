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
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

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
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = _stdlib_logging.getLogger("axonpush")


def create_axonpush_loguru_sink(
    *,
    client: "AxonPush | AsyncAxonPush",
    channel_id: int,
    source: str = "app",
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    environment: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> Callable[[Any], None]:
    """Build a Loguru sink callable that forwards each record to AxonPush.

    Pass the returned function to ``logger.add(sink, serialize=True)``.
    The ``serialize=True`` flag is **required** — it tells Loguru to pass
    a JSON string of the record to the sink, which we parse here.
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

    def sink(message: Any) -> None:
        """Loguru calls this with a Message object whose .record attribute
        contains the structured record. With ``serialize=True`` the message
        also has a JSON string representation."""
        try:
            # When serialize=True, the message itself is a JSON string
            record_dict: Dict[str, Any]
            if isinstance(message, str):
                record_dict = json.loads(message).get("record", {})
            else:
                # Loguru Message object — has a .record attribute
                record_dict = getattr(message, "record", {}) or {}

            level_name = (
                record_dict.get("level", {}).get("name", "INFO")
                if isinstance(record_dict.get("level"), dict)
                else str(record_dict.get("level", "INFO"))
            )
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
            if "process" in record_dict:
                proc = record_dict["process"]
                if isinstance(proc, dict) and "id" in proc:
                    attributes["process.pid"] = proc["id"]
            if "thread" in record_dict:
                thr = record_dict["thread"]
                if isinstance(thr, dict) and "name" in thr:
                    attributes["thread.name"] = thr["name"]

            # Loguru's `extra` dict carries user-supplied bound context
            extra = record_dict.get("extra")
            if isinstance(extra, dict):
                for key, value in extra.items():
                    attributes[key] = value

            # Exception info
            exception = record_dict.get("exception")
            if isinstance(exception, dict):
                if "type" in exception:
                    attributes["exception.type"] = exception["type"]
                if "value" in exception:
                    attributes["exception.message"] = exception["value"]

            # timeUnixNano: loguru records have a 'time' field which is a
            # datetime when serialize=False or an ISO/repr string + timestamp
            # when serialize=True. Try to get the unix timestamp.
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
                resource=resource_or_none,
            )

            trace = current_trace() or get_or_create_trace()

            result = client.events.publish(  # type: ignore[union-attr]
                identifier=str(record_dict.get("name", "loguru")),
                payload=payload,
                channel_id=channel_id,
                agent_id=agent_id,
                trace_id=trace.trace_id,
                span_id=trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "loguru"},
            )

            if hasattr(result, "__await__"):
                try:
                    import asyncio

                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
        except Exception as exc:
            _internal_logger.warning("AxonPush loguru sink failed: %s", exc)

    return sink
