"""Unit tests for the OpenTelemetry SpanExporter integration."""
from __future__ import annotations

import json

import httpx
import pytest

pytest.importorskip("opentelemetry.sdk.trace")

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import (  # noqa: E402
    SimpleSpanProcessor,
    SpanExportResult,
)

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.otel import AxonPushSpanExporter  # noqa: E402

from tests.conftest import API_KEY, BASE_URL, TENANT_ID  # noqa: E402


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "span",
            "payload": {},
            "eventType": "app.span",
        },
    )


def _bodies(route):
    return [json.loads(call.request.content) for call in route.calls]


def test_exporter_publishes_app_span_event(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(
            client=c, channel_id=5, service_name="otel-svc"
        )
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        # Use a fresh provider rather than mutating the global one
        tracer = provider.get_tracer(__name__)

        with tracer.start_as_current_span("POST /chat") as span:
            span.set_attribute("http.method", "POST")
            span.set_attribute("http.status_code", 200)

        provider.shutdown()

    bodies = _bodies(route)
    assert len(bodies) == 1
    body = bodies[0]
    assert body["channel_id"] == 5
    assert body["eventType"] == "app.span"
    assert body["identifier"] == "POST /chat"
    assert body["metadata"]["framework"] == "opentelemetry"

    p = body["payload"]
    assert p["name"] == "POST /chat"
    assert "traceId" in p
    assert "spanId" in p
    assert len(p["traceId"]) == 32  # 128-bit hex
    assert len(p["spanId"]) == 16  # 64-bit hex
    assert p["startTimeUnixNano"] is not None
    assert p["endTimeUnixNano"] is not None
    assert p["status"]["code"] == 0  # UNSET by default
    assert p["attributes"]["http.method"] == "POST"
    assert p["attributes"]["http.status_code"] == 200
    assert p["resource"]["service.name"] == "otel-svc"


def test_exporter_returns_success_on_happy_path(mock_router):
    mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        provider = TracerProvider()
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("op") as span:
            pass
        # ReadableSpan list — call exporter directly to capture the result
        # SimpleSpanProcessor calls export() under the hood, but we want
        # to assert the return value here.
        readable = [span]  # the just-ended span IS a ReadableSpan
        result = exporter.export(readable)
    assert result == SpanExportResult.SUCCESS


def test_exporter_returns_success_when_per_span_publish_fails(mock_router):
    """``_export_one`` wraps each publish in its own try/except, so a failing
    publish must NOT propagate up into ``export()``. The exporter contract is
    that one bad span never breaks the OTel SDK's batch flush — the user's
    tracing pipeline keeps running.
    """
    mock_router.post("/event").mock(side_effect=RuntimeError("boom"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        provider = TracerProvider()
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("op") as span:
            pass
        result = exporter.export([span])
    assert result == SpanExportResult.SUCCESS


def test_exporter_returns_failure_when_export_loop_crashes(mock_router):
    """The OUTER try/except in ``export()`` only fires if iterating ``spans``
    itself raises (e.g. a malformed Sequence). Verify that contract: a non-
    iterable input → FAILURE, not a crash.
    """
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        # Passing something that raises on iteration
        class _BadSpans:
            def __iter__(self):
                raise RuntimeError("iter blew up")
        result = exporter.export(_BadSpans())  # type: ignore[arg-type]
    assert result == SpanExportResult.FAILURE


def test_parent_span_id_propagated(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer(__name__)

        with tracer.start_as_current_span("parent"):
            with tracer.start_as_current_span("child"):
                pass
        provider.shutdown()

    bodies = _bodies(route)
    assert len(bodies) == 2
    # SimpleSpanProcessor exports children before parents
    child_body = next(b for b in bodies if b["payload"]["name"] == "child")
    parent_body = next(b for b in bodies if b["payload"]["name"] == "parent")
    assert "parentSpanId" in child_body["payload"]
    assert child_body["payload"]["parentSpanId"] == parent_body["payload"]["spanId"]
    assert "parentSpanId" not in parent_body["payload"]


def test_force_flush_returns_true(mock_router):
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        assert exporter.force_flush() is True


def test_shutdown_is_noop(mock_router):
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        exporter = AxonPushSpanExporter(client=c, channel_id=5)
        assert exporter.shutdown() is None
