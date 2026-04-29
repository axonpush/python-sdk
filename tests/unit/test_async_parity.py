"""Sync and async clients must produce identical request payloads.

If they ever diverge, users who switch from AxonPush → AsyncAxonPush will
get subtly different behavior. This test pins them to the same shape.
"""
from __future__ import annotations

import json

import httpx

from axonpush import AsyncAxonPush, AxonPush, EventType

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _success():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "x",
            "payload": {},
            "eventType": "custom",
        },
    )


async def test_sync_and_async_produce_identical_publish_body(mock_router):
    route = mock_router.post("/event").mock(return_value=_success())

    common_kwargs = dict(
        identifier="parity_check",
        payload={"a": 1, "b": [1, 2, 3]},
        channel_id=5,
        agent_id="bot",
        trace_id="tr_fixed_trace_id",
        span_id="sp_fixed",
        event_type=EventType.AGENT_MESSAGE,
        metadata={"src": "test"},
    )

    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        c.events.publish(**common_kwargs)
    sync_body = json.loads(route.calls.last.request.content)

    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as c:
        await c.events.publish(**common_kwargs)
    async_body = json.loads(route.calls.last.request.content)

    assert sync_body == async_body
