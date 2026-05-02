"""OpenTelemetry SpanExporter for AxonPush.

Implements the OTel ``SpanExporter`` interface so any service already
instrumented with the OpenTelemetry SDK can ship spans to AxonPush by
plugging this exporter into its tracer provider.

The exporter ingests through the regular AxonPush events API
(``client.events.publish`` with ``event_type=EventType.APP_SPAN``)
rather than the dedicated OTLP ``/v1/traces`` endpoint. The dedicated
endpoint exists on the backend (see :file:`src/otlp/otlp.controller.ts`)
and accepts both protobuf and JSON, but the per-span ``app.span`` events
flow gives uniform fan-out / channel routing for free. Future versions
may add a direct OTLP transport.

Tested against ``opentelemetry-sdk>=1.20,<2``.

Install::

    pip install axonpush[otel]

Usage::

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from axonpush import AxonPush
    from axonpush.integrations.otel import AxonPushSpanExporter

    client = AxonPush(api_key="ak_...", tenant_id="org_...")
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(
            AxonPushSpanExporter(
                client=client,
                channel_id="ch_...",
                service_name="my-api",
            )
        )
    )
    trace.set_tracer_provider(provider)
"""

from __future__ import annotations

import logging as _stdlib_logging
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional, Sequence

try:
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
except ImportError:
    raise ImportError(
        "OTel exporter requires the 'otel' extra. Install it with: pip install axonpush[otel]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._otel_payload import _stringify_values
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    detect_serverless,
    flush_after_invocation,
)
from axonpush.integrations._utils import (
    build_resource,
    coerce_channel_id,
    fire_and_forget,
    is_async_client,
)
from axonpush.models import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

__all__ = ["AxonPushSpanExporter", "flush_after_invocation"]

_internal_logger = _stdlib_logging.getLogger("axonpush")


class AxonPushSpanExporter(SpanExporter):
    """A ``SpanExporter`` that ships :class:`ReadableSpan` to AxonPush as ``app.span`` events."""

    def __init__(
        self,
        *,
        client: "AxonPush | AsyncAxonPush",
        channel_id: int | str,
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        environment: Optional[str] = None,
        mode: Optional[Literal["background", "sync"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
    ) -> None:
        resolved_mode = mode or "background"
        if resolved_mode not in ("background", "sync"):
            raise ValueError(f"mode must be 'background' or 'sync', got {resolved_mode!r}")

        self._client = client
        self._channel_id = coerce_channel_id(channel_id)
        self._trace = get_or_create_trace()
        self._environment = environment

        self._resource_override = build_resource(service_name, service_version, environment) or {}

        if resolved_mode == "background":
            if is_async_client(client):
                self._publisher: Optional[BackgroundPublisher] = None
            else:
                self._publisher = BackgroundPublisher(
                    client,  # type: ignore[arg-type]
                    queue_size=queue_size,
                    shutdown_timeout=shutdown_timeout,
                )
        else:
            self._publisher = None

        serverless = detect_serverless()
        if serverless is not None and self._publisher is not None:
            _internal_logger.info(
                "AxonPush detected %s. Call exporter.flush() at the end of "
                "each invocation (or wrap your handler with "
                "axonpush.integrations.otel.flush_after_invocation) to "
                "avoid losing spans when the container is frozen.",
                serverless,
            )

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            for span in spans:
                self._export_one(span)
            return SpanExportResult.SUCCESS
        except Exception as exc:
            _internal_logger.warning("AxonPush OTel exporter failed: %s", exc)
            return SpanExportResult.FAILURE

    def flush(self, timeout: Optional[float] = None) -> None:
        """Block until queued spans are published, or until ``timeout``."""
        if self._publisher is not None:
            self._publisher.flush(timeout)

    def shutdown(self) -> None:
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        self.flush(timeout=timeout_millis / 1000.0)
        return True

    def _export_one(self, span: ReadableSpan) -> None:
        ctx = span.get_span_context()  # type: ignore[no-untyped-call]
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        parent_span_id: Optional[str] = None
        parent = span.parent
        if parent is not None:
            parent_span_id = format(parent.span_id, "016x")

        # status code matches OTel proto: 0=UNSET 1=OK 2=ERROR
        status_code = int(span.status.status_code.value) if span.status else 0
        status_message = span.status.description or "" if span.status else ""

        attributes: Dict[str, Any] = {}
        if span.attributes:
            for key, value in span.attributes.items():
                attributes[key] = value

        resource: Dict[str, Any] = {}
        if span.resource and span.resource.attributes:
            for key, value in span.resource.attributes.items():
                resource[key] = value
        resource.update(self._resource_override)

        events_out = []
        for ev in span.events or []:
            ev_attrs: Dict[str, Any] = {}
            if ev.attributes:
                for key, value in ev.attributes.items():
                    ev_attrs[key] = value
            events_out.append(
                {
                    "timeUnixNano": str(ev.timestamp),
                    "name": ev.name,
                    "attributes": _stringify_values(ev_attrs),
                }
            )

        links_out = []
        for link in span.links or []:
            link_attrs: Dict[str, Any] = {}
            if link.attributes:
                for key, value in link.attributes.items():
                    link_attrs[key] = value
            links_out.append(
                {
                    "traceId": format(link.context.trace_id, "032x"),
                    "spanId": format(link.context.span_id, "016x"),
                    "attributes": _stringify_values(link_attrs),
                }
            )

        kind_value = int(span.kind.value) if span.kind else 0

        payload: Dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": span.name,
            "kind": kind_value,
            "startTimeUnixNano": str(span.start_time) if span.start_time else None,
            "endTimeUnixNano": str(span.end_time) if span.end_time else None,
            "status": {"code": status_code, "message": status_message},
            "attributes": _stringify_values(attributes),
        }
        if parent_span_id:
            payload["parentSpanId"] = parent_span_id
        if events_out:
            payload["events"] = events_out
        if links_out:
            payload["links"] = links_out
        if resource:
            payload["resource"] = _stringify_values(resource)

        scope = getattr(span, "instrumentation_scope", None)
        if scope is not None:
            payload["scope"] = {
                "name": getattr(scope, "name", None),
                "version": getattr(scope, "version", None),
            }

        publish_kwargs: Dict[str, Any] = {
            "identifier": span.name,
            "payload": payload,
            "channel_id": self._channel_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "event_type": EventType.APP_SPAN,
            "metadata": {"framework": "opentelemetry"},
        }
        if parent_span_id:
            publish_kwargs["parent_event_id"] = parent_span_id
        if self._environment is not None:
            publish_kwargs["environment"] = self._environment

        if self._publisher is not None:
            self._publisher.submit(publish_kwargs)
            return

        try:
            result = self._client.events.publish(**publish_kwargs)
            fire_and_forget(result)
        except Exception as exc:
            _internal_logger.warning("AxonPush OTel exporter publish failed: %s", exc)
