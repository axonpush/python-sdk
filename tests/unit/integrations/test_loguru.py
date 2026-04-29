"""Unit tests for the Loguru integration.

Skipped automatically if the ``loguru`` extra isn't installed."""
from __future__ import annotations

import json

import httpx
import pytest

pytest.importorskip("loguru")

from loguru import logger as loguru_logger  # noqa: E402

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.loguru import create_axonpush_loguru_sink  # noqa: E402

from tests.conftest import API_KEY, BASE_URL, TENANT_ID  # noqa: E402


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "x",
            "payload": {},
            "eventType": "app.log",
        },
    )


def _last_body(route) -> dict:
    return json.loads(route.calls.last.request.content)


@pytest.fixture(autouse=True)
def reset_loguru():
    """Loguru has a global logger; remove all handlers before/after each test."""
    loguru_logger.remove()
    yield
    loguru_logger.remove()


def test_sink_emits_app_log(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        sink = create_axonpush_loguru_sink(
            client=c, channel_id=5, service_name="loguru-svc", mode="sync"
        )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.error("connection refused")

    body = _last_body(route)
    assert body["channel_id"] == 5
    assert body["eventType"] == "app.log"
    assert body["payload"]["severityText"] == "ERROR"
    assert body["payload"]["severityNumber"] == 17
    assert body["payload"]["body"] == "connection refused"
    assert body["payload"]["resource"]["service.name"] == "loguru-svc"
    assert body["metadata"]["framework"] == "loguru"


def test_severity_mapping(mock_router):
    """Each Loguru level → expected OTel severity number.

    Assert call_count grows by 1 per iteration so a silently dropped level
    can't pass against stale data.
    """
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        loguru_logger.add(
            create_axonpush_loguru_sink(client=c, channel_id=5, mode="sync"),
            serialize=True,
            level="DEBUG",  # explicit so DEBUG isn't filtered by the sink
        )
        cases = [
            (loguru_logger.debug, 5, "DEBUG"),
            (loguru_logger.info, 9, "INFO"),
            (loguru_logger.warning, 13, "WARN"),
            (loguru_logger.error, 17, "ERROR"),
            (loguru_logger.critical, 21, "FATAL"),
        ]
        expected_calls = 0
        for log_fn, expected_num, expected_text in cases:
            log_fn("msg")
            expected_calls += 1
            assert route.call_count == expected_calls, (
                f"expected loguru sink to emit for {expected_text}, "
                f"but route.call_count is {route.call_count}"
            )
            body = _last_body(route)
            assert body["payload"]["severityNumber"] == expected_num
            assert body["payload"]["severityText"] == expected_text


def test_bound_extra_becomes_attributes(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        loguru_logger.add(
            create_axonpush_loguru_sink(client=c, channel_id=5, mode="sync"),
            serialize=True,
        )
        loguru_logger.bind(user_id=42, request_id="abc").info("hello")

    attrs = _last_body(route)["payload"]["attributes"]
    assert attrs["user_id"] == 42
    assert attrs["request_id"] == "abc"


def test_agent_source(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        loguru_logger.add(
            create_axonpush_loguru_sink(client=c, channel_id=5, source="agent", mode="sync"),
            serialize=True,
        )
        loguru_logger.info("agent log")
    assert _last_body(route)["eventType"] == "agent.log"


def test_invalid_source_rejected():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(ValueError, match="source must be"):
            create_axonpush_loguru_sink(client=c, channel_id=5, source="bogus", mode="sync")


def test_sink_swallows_publish_errors(mock_router):
    """Sink must NOT raise — would crash the user's app via Loguru's pipeline."""
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("nope"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        loguru_logger.add(
            create_axonpush_loguru_sink(client=c, channel_id=5, mode="sync"),
            serialize=True,
        )
        loguru_logger.error("should not crash")
