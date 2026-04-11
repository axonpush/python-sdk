"""OpenTelemetry SpanExporter for AxonPush.

Implements the OTel ``SpanExporter`` interface so any Python service already
instrumented with the OpenTelemetry SDK can ship spans to AxonPush by adding
this exporter to its tracer provider.

Requires: ``pip install axonpush[otel]``

Usage::

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from axonpush import AxonPush
    from axonpush.integrations.otel import AxonPushSpanExporter

    client = AxonPush(api_key="ak_...", tenant_id="1")
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(
            AxonPushSpanExporter(
                client=client,
                channel_id=1,
                service_name="my-api",
            )
        )
    )
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("POST /chat") as span:
        span.set_attribute("http.method", "POST")
        ...
"""
from __future__ import annotations

import logging as _stdlib_logging
from typing import Any, Dict, Optional, Sequence, TYPE_CHECKING

try:
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
except ImportError:
    raise ImportError(
        "OTel exporter requires the 'otel' extra. "
        "Install it with: pip install axonpush[otel]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._otel_payload import _stringify_values
from axonpush.models.events import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

_internal_logger = _stdlib_logging.getLogger("axonpush")


class AxonPushSpanExporter(SpanExporter):
    """A ``SpanExporter`` that ships ReadableSpans to AxonPush as ``app.span`` events."""

    def __init__(
        self,
        *,
        client: "AxonPush | AsyncAxonPush",
        channel_id: int,
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._trace = get_or_create_trace()

        resource: Dict[str, Any] = {}
        if service_name is not None:
            resource["service.name"] = service_name
        if service_version is not None:
            resource["service.version"] = service_version
        if environment is not None:
            resource["deployment.environment"] = environment
        self._resource_override = resource

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            for span in spans:
                self._export_one(span)
            return SpanExportResult.SUCCESS
        except Exception as exc:
            _internal_logger.warning("AxonPush OTel exporter failed: %s", exc)
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # noqa: ARG002
        return True

    def _export_one(self, span: ReadableSpan) -> None:
        ctx = span.get_span_context()  # type: ignore[no-untyped-call]
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        parent_span_id: Optional[str] = None
        parent = span.parent
        if parent is not None:
            parent_span_id = format(parent.span_id, "016x")

        # status — extract code as integer (matches OTel proto: 0=UNSET 1=OK 2=ERROR)
        status_code = int(span.status.status_code.value) if span.status else 0
        status_message = span.status.description or "" if span.status else ""

        # attributes — convert to plain dict
        attributes: Dict[str, Any] = {}
        if span.attributes:
            for key, value in span.attributes.items():
                attributes[key] = value

        # resource attributes — combine span resource with exporter override
        resource: Dict[str, Any] = {}
        if span.resource and span.resource.attributes:
            for key, value in span.resource.attributes.items():
                resource[key] = value
        resource.update(self._resource_override)

        # events
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

        # links
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

        # span.kind is an enum — extract the integer value
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

        try:
            result = self._client.events.publish(
                identifier=span.name,
                payload=payload,
                channel_id=self._channel_id,
                trace_id=trace_id,
                span_id=span_id,
                event_type=EventType.APP_SPAN,
                metadata={"framework": "opentelemetry"},
            )
            import asyncio

            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(result)
                except RuntimeError:
                    pass
        except Exception as exc:
            _internal_logger.warning(
                "AxonPush OTel exporter publish failed: %s", exc
            )
