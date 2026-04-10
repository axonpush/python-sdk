"""Unit tests for the print_capture integration.

Verifies that ``setup_print_capture()`` patches stdout/stderr to forward each
newline-terminated write to AxonPush as an OTel-shaped log event, and that
``unpatch()`` restores the original streams.
"""
from __future__ import annotations

import json
import sys

import httpx
import pytest

from axonpush import AxonPush
from axonpush.integrations.print_capture import setup_print_capture

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "print",
            "payload": {},
            "channel_id": 5,
            "eventType": "agent.log",
        },
    )


def _bodies(route):
    return [json.loads(call.request.content) for call in route.calls]


@pytest.fixture()
def restore_stdio():
    """Save and restore real stdio in case a test forgets to unpatch."""
    orig_out, orig_err = sys.stdout, sys.stderr
    yield
    sys.stdout, sys.stderr = orig_out, orig_err


def test_print_emits_one_event_per_line(mock_router, restore_stdio):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)
        try:
            print("first line")
            print("second line")
        finally:
            handle.unpatch()

    bodies = _bodies(route)
    assert len(bodies) == 2
    assert bodies[0]["payload"]["body"] == "first line"
    assert bodies[1]["payload"]["body"] == "second line"
    assert bodies[0]["payload"]["severityText"] == "INFO"
    assert bodies[0]["payload"]["severityNumber"] == 9
    assert bodies[0]["metadata"]["framework"] == "print-capture"


def test_stderr_is_error_severity(mock_router, restore_stdio):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)
        try:
            print("oops", file=sys.stderr)
        finally:
            handle.unpatch()

    body = _bodies(route)[0]
    assert body["payload"]["severityText"] == "ERROR"
    assert body["payload"]["severityNumber"] == 17
    assert body["payload"]["attributes"]["log.iostream"] == "stderr"


def test_partial_line_buffered_until_newline(mock_router, restore_stdio):
    """Writes without a newline must be buffered, not emitted as fragments."""
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)
        try:
            sys.stdout.write("hello ")
            assert not route.called  # nothing emitted yet
            sys.stdout.write("world\n")
        finally:
            handle.unpatch()

    bodies = _bodies(route)
    assert len(bodies) == 1
    assert bodies[0]["payload"]["body"] == "hello world"


def test_blank_lines_skipped(mock_router, restore_stdio):
    """Empty/whitespace-only lines should not produce events (noise reduction)."""
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)
        try:
            print("")
            print("   ")
            print("real content")
        finally:
            handle.unpatch()

    bodies = _bodies(route)
    assert len(bodies) == 1
    assert bodies[0]["payload"]["body"] == "real content"


def test_unpatch_restores_streams(mock_router, restore_stdio):
    mock_router.post("/event").mock(return_value=_ack())
    orig_out, orig_err = sys.stdout, sys.stderr
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)
        assert sys.stdout is not orig_out
        assert sys.stderr is not orig_err
        handle.unpatch()
    assert sys.stdout is orig_out
    assert sys.stderr is orig_err


def test_event_type_app_when_source_app(mock_router, restore_stdio):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5, source="app")
        try:
            print("hi")
        finally:
            handle.unpatch()
    assert _bodies(route)[0]["eventType"] == "app.log"


def test_event_type_agent_by_default(mock_router, restore_stdio):
    route = mock_router.post("/event").mock(return_value=_ack())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        handle = setup_print_capture(c, channel_id=5)  # default source="agent"
        try:
            print("hi")
        finally:
            handle.unpatch()
    assert _bodies(route)[0]["eventType"] == "agent.log"


def test_invalid_source_rejected(restore_stdio):
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(ValueError, match="source must be"):
            setup_print_capture(c, channel_id=5, source="bogus")


def test_publish_failure_does_not_crash_print(mock_router, restore_stdio):
    """A flaky publish must NOT propagate to the user's print() call."""
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("nope"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        handle = setup_print_capture(c, channel_id=5)
        try:
            print("should still work")  # must not raise
        finally:
            handle.unpatch()
