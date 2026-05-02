"""End-to-end round-trip tests for the 5 logging integrations.

Each test wires the integration to the live easy-push backend, emits one
event, then asserts the event appears in client.events.list() with the
expected OTel-shaped payload. This catches payload-shape mismatches that
the respx-mocked unit tests in tests/unit/integrations/ can't see.
"""

from __future__ import annotations

import logging
import sys
import time

import pytest

from axonpush import EventType
from axonpush.integrations.logging_handler import AxonPushLoggingHandler
from axonpush.integrations.print_capture import setup_print_capture

pytestmark = pytest.mark.e2e


def _find_by_body(events, body):
    return [e for e in events if e.payload.get("body") == body]


def test_logging_handler_round_trip(client, channel):
    logger = logging.getLogger(f"e2e.logging.{channel.id}")
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = AxonPushLoggingHandler(client=client, channel_id=channel.id, service_name="e2e-svc")
    logger.addHandler(handler)
    try:
        logger.error("connection refused", extra={"user_id": 42})
        time.sleep(0.5)
    finally:
        logger.removeHandler(handler)

    events = client.events.list(channel.id, limit=50)
    matches = _find_by_body(events, "connection refused")
    assert len(matches) == 1, (
        f"expected one matching event, got payloads: {[e.payload for e in events]}"
    )
    e = matches[0]
    assert e.event_type == EventType.APP_LOG
    assert e.payload["severityText"] == "ERROR"
    assert e.payload["severityNumber"] == 17
    assert e.payload["attributes"]["user_id"] == 42
    assert e.payload["resource"]["service.name"] == "e2e-svc"
    assert e.metadata["framework"] == "stdlib-logging"


def test_loguru_sink_round_trip(client, channel):
    pytest.importorskip("loguru")
    from loguru import logger as loguru_logger

    from axonpush.integrations.loguru import create_axonpush_loguru_sink

    loguru_logger.remove()
    sink = create_axonpush_loguru_sink(
        client=client, channel_id=channel.id, service_name="loguru-e2e"
    )
    loguru_logger.add(sink, serialize=True, level="DEBUG")
    try:
        loguru_logger.error("loguru round trip")
        time.sleep(0.5)
    finally:
        loguru_logger.remove()

    matches = _find_by_body(client.events.list(channel.id, limit=50), "loguru round trip")
    assert len(matches) == 1
    assert matches[0].event_type == EventType.APP_LOG
    assert matches[0].payload["severityText"] == "ERROR"
    assert matches[0].payload["resource"]["service.name"] == "loguru-e2e"
    assert matches[0].metadata["framework"] == "loguru"


def test_structlog_processor_round_trip(client, channel):
    pytest.importorskip("structlog")
    import structlog

    from axonpush.integrations.structlog import axonpush_structlog_processor

    structlog.reset_defaults()
    forwarder = axonpush_structlog_processor(client=client, channel_id=channel.id)
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            forwarder,
            structlog.processors.JSONRenderer(),
        ],
    )
    try:
        log = structlog.get_logger()
        log.error("structlog round trip", user_id=7)
        time.sleep(0.5)
    finally:
        structlog.reset_defaults()

    matches = _find_by_body(client.events.list(channel.id, limit=50), "structlog round trip")
    assert len(matches) == 1
    assert matches[0].event_type == EventType.APP_LOG
    assert matches[0].payload["attributes"]["user_id"] == 7
    assert matches[0].metadata["framework"] == "structlog"


def test_print_capture_round_trip(client, channel):
    orig_out, orig_err = sys.stdout, sys.stderr
    handle = setup_print_capture(client, channel_id=channel.id, source="app")
    try:
        print("hello from print_capture")
    finally:
        handle.unpatch()
        sys.stdout, sys.stderr = orig_out, orig_err
    time.sleep(0.5)

    matches = _find_by_body(client.events.list(channel.id, limit=50), "hello from print_capture")
    assert len(matches) == 1
    assert matches[0].payload["severityText"] == "INFO"
    assert matches[0].payload["severityNumber"] == 9
    assert matches[0].payload["attributes"]["log.iostream"] == "stdout"
    assert matches[0].metadata["framework"] == "print-capture"


def test_otel_span_exporter_round_trip(client, channel):
    pytest.importorskip("opentelemetry.sdk.trace")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    from axonpush.integrations.otel import AxonPushSpanExporter

    provider = TracerProvider()
    provider.add_span_processor(
        SimpleSpanProcessor(
            AxonPushSpanExporter(client=client, channel_id=channel.id, service_name="otel-e2e")
        )
    )
    tracer = provider.get_tracer(__name__)
    with tracer.start_as_current_span("e2e-span") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.status_code", 200)
    provider.shutdown()
    time.sleep(0.5)

    events = client.events.list(channel.id, limit=50)
    spans = [
        e
        for e in events
        if e.event_type == EventType.APP_SPAN and e.payload.get("name") == "e2e-span"
    ]
    assert len(spans) == 1
    p = spans[0].payload
    assert p["attributes"]["http.method"] == "POST"
    assert p["attributes"]["http.status_code"] == 200
    assert p["resource"]["service.name"] == "otel-e2e"
    assert len(p["traceId"]) == 32  # 128-bit hex
    assert len(p["spanId"]) == 16  # 64-bit hex
    assert spans[0].metadata["framework"] == "opentelemetry"
