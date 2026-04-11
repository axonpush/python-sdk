"""Unit tests for the structlog integration."""
from __future__ import annotations

import copy
import json

import httpx
import pytest

pytest.importorskip("structlog")

import structlog  # noqa: E402

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.structlog import axonpush_structlog_processor  # noqa: E402

from tests.conftest import API_KEY, BASE_URL, TENANT_ID  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_structlog():
    """structlog.configure() is global state. Reset before AND after each test
    so test order doesn't change behavior."""
    structlog.reset_defaults()
    try:
        yield
    finally:
        structlog.reset_defaults()


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "structlog",
            "payload": {},
            "eventType": "app.log",
        },
    )


def _last_body(route) -> dict:
    return json.loads(route.calls.last.request.content)


def test_processor_publishes_event(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(
            client=c, channel_id=5, service_name="structlog-svc", mode="sync"
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
    (e.g. JSONRenderer) need to see the original keys AND values intact.

    The processor returns the same dict instance, so a key-only check would
    be aliased and meaningless. We deepcopy a snapshot before the call and
    compare the full dict contents after.
    """
    mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5, mode="sync")
        event_dict = {
            "event": "hello",
            "level": "info",
            "timestamp": "2026-04-11T12:00:00",
            "user_id": 7,
            "nested": {"a": 1, "b": [2, 3]},
        }
        snapshot = copy.deepcopy(event_dict)
        result = forwarder(None, "info", event_dict)
        # Same instance returned (pass-through, not a copy)
        assert result is event_dict
        # No keys added/removed AND no values mutated
        assert event_dict == snapshot


def test_severity_from_method_name_when_level_missing(mock_router):
    """If add_log_level isn't in the chain, fall back to the method name."""
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5, mode="sync")
        forwarder(None, "warning", {"event": "stale cache"})
    body = _last_body(route)
    assert body["payload"]["severityText"] == "WARN"
    assert body["payload"]["severityNumber"] == 13


def test_agent_source(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        forwarder = axonpush_structlog_processor(
            client=c, channel_id=5, source="agent", mode="sync"
        )
        forwarder(None, "info", {"event": "agent log"})
    assert _last_body(route)["eventType"] == "agent.log"


def test_invalid_source_rejected():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(ValueError, match="source must be"):
            axonpush_structlog_processor(client=c, channel_id=5, source="bogus", mode="sync")


def test_processor_swallows_publish_errors(mock_router):
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("nope"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        forwarder = axonpush_structlog_processor(client=c, channel_id=5, mode="sync")
        # Should not raise even on transport failure
        result = forwarder(None, "error", {"event": "boom"})
    assert result == {"event": "boom"}
