"""Unit tests for ``axonpush.realtime.sse.SSESubscription``.

Mocks the SSE stream via respx and verifies the subscription parses framed
``message`` events into ``Event`` models. Previously this code path was
covered only by e2e tests.
"""
from __future__ import annotations

import json

import httpx
import pytest

from axonpush import AxonPush, EventType
from axonpush.models.events import Event
from axonpush.realtime.sse import SSESubscription

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _sse_frame(event: str, data: dict) -> bytes:
    """Build one SSE frame in the wire format httpx-sse expects."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode()


def _sse_stream(*frames: bytes) -> bytes:
    return b"".join(frames)


def test_sse_yields_parsed_events(mock_router):
    payload1 = {
        "id": 1,
        "identifier": "tick",
        "payload": {"n": 1},
        "eventType": "agent.message",
    }
    payload2 = {
        "id": 2,
        "identifier": "tock",
        "payload": {"n": 2},
        "eventType": "agent.message",
    }
    body = _sse_stream(
        _sse_frame("message", payload1),
        _sse_frame("message", payload2),
    )
    mock_router.get("/channel/5/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body,
        )
    )

    received: list[Event] = []
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        sub = SSESubscription(c._transport, channel_id=5)
        with sub as s:
            for evt in s:
                received.append(evt)

    assert len(received) == 2
    assert received[0].identifier == "tick"
    assert received[0].event_type == EventType.AGENT_MESSAGE
    assert received[1].identifier == "tock"


def test_sse_skips_non_message_events(mock_router):
    """Non-``message`` SSE events (e.g. ``ping``, ``error``) must be ignored —
    they're framing/keepalive, not application data."""
    body = _sse_stream(
        b"event: ping\ndata: \n\n",
        _sse_frame(
            "message",
            {
                "id": 1,
                "identifier": "real",
                "payload": {},
                "eventType": "custom",
            },
        ),
        b"event: heartbeat\ndata: \n\n",
    )
    mock_router.get("/channel/5/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body,
        )
    )

    received: list[Event] = []
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with SSESubscription(c._transport, channel_id=5) as sub:
            for evt in sub:
                received.append(evt)

    assert len(received) == 1
    assert received[0].identifier == "real"


def test_sse_skips_malformed_json(mock_router):
    """Malformed JSON in a message frame must NOT crash the subscription —
    the bad frame is dropped and iteration continues."""
    body = _sse_stream(
        b"event: message\ndata: {not json\n\n",
        _sse_frame(
            "message",
            {
                "id": 1,
                "identifier": "valid",
                "payload": {},
                "eventType": "custom",
            },
        ),
    )
    mock_router.get("/channel/5/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=body,
        )
    )

    received: list[Event] = []
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with SSESubscription(c._transport, channel_id=5) as sub:
            for evt in sub:
                received.append(evt)

    assert len(received) == 1
    assert received[0].identifier == "valid"


def test_sse_uses_event_identifier_path(mock_router):
    """If ``event_identifier`` is set, the subscription should hit
    ``/channel/{id}/{name}/subscribe`` rather than the bare path."""
    route = mock_router.get("/channel/5/heartbeat/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"",
        )
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with SSESubscription(
            c._transport, channel_id=5, event_identifier="heartbeat"
        ) as sub:
            list(sub)  # drain
    assert route.called


def test_sse_filter_params_sent_as_query_string(mock_router):
    """Filters (agent_id, event_type, trace_id) must land in the query string."""
    route = mock_router.get("/channel/5/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"",
        )
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with SSESubscription(
            c._transport,
            channel_id=5,
            agent_id="bot",
            event_type=EventType.AGENT_TOOL_CALL_START,
            trace_id="tr_abc",
        ) as sub:
            list(sub)
    params = route.calls.last.request.url.params
    assert params.get("agentId") == "bot"
    assert params.get("eventType") == "agent.tool_call.start"
    assert params.get("traceId") == "tr_abc"


def test_sse_iter_outside_context_manager_raises(mock_router):
    """Iterating without entering the context manager should raise
    RuntimeError, not silently yield nothing."""
    mock_router.get("/channel/5/subscribe").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=b"",
        )
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        sub = SSESubscription(c._transport, channel_id=5)
        with pytest.raises(RuntimeError, match="context manager"):
            for _ in sub:
                pass
