"""Unit tests for the structlog integration."""
from __future__ import annotations

import json

import httpx
import pytest

pytest.importorskip("structlog")

import structlog  # noqa: E402

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.structlog import axonpush_structlog_processor  # noqa: E402

from tests.conftest import API_KEY, BASE_URL, TENANT_ID  # noqa: E402


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "structlog",
            "payload": {},
            "channel_id": 5,
            "eventType": "app.log",
        },
    )


def _last_body(route) -> dict:
    return json.loads(route.calls.last.request.content)


def test_processor_publishes_event(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(
            client=c, channel_id=5, service_name="structlog-svc"
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

    body = _last_body(route)
    assert body["channel_id"] == 5
    assert body["eventType"] == "app.log"
    assert body["payload"]["severityText"] == "ERROR"
    assert body["payload"]["severityNumber"] == 17
    assert body["payload"]["body"] == "connection refused"
    assert body["payload"]["resource"]["service.name"] == "structlog-svc"
    assert body["metadata"]["framework"] == "structlog"
    # User-supplied bound context lands in attributes
    assert body["payload"]["attributes"]["user_id"] == 42


def test_processor_is_non_destructive(mock_router):
    """The processor must NOT mutate the event_dict — downstream processors
    (e.g. JSONRenderer) need to see the original keys."""
    mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5)
        event_dict = {
            "event": "hello",
            "level": "info",
            "timestamp": "2026-04-11T12:00:00",
            "user_id": 7,
        }
        # Snapshot the contents (the function returns the same dict instance,
        # so we copy to make the assertion meaningful)
        original_keys = set(event_dict.keys())
        result = forwarder(None, "info", event_dict)
        assert set(result.keys()) == original_keys
        assert result["event"] == "hello"
        assert result["user_id"] == 7


def test_severity_from_method_name_when_level_missing(mock_router):
    """If add_log_level isn't in the chain, fall back to the method name."""
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5)
        forwarder(None, "warning", {"event": "stale cache"})
    body = _last_body(route)
    assert body["payload"]["severityText"] == "WARN"
    assert body["payload"]["severityNumber"] == 13


def test_agent_source(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(
            client=c, channel_id=5, source="agent"
        )
        forwarder(None, "info", {"event": "agent log"})
    assert _last_body(route)["eventType"] == "agent.log"


def test_invalid_source_rejected():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(ValueError, match="source must be"):
            axonpush_structlog_processor(client=c, channel_id=5, source="bogus")


def test_processor_swallows_publish_errors(mock_router):
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("nope"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5)
        # Should not raise even on transport failure
        result = forwarder(None, "error", {"event": "boom"})
    assert result == {"event": "boom"}
