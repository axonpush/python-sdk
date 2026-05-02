"""Validates that the integration handlers correctly schedule async publishes
when given an AsyncAxonPush client. The unit tests cover the
``loop.create_task(result)`` branch with respx mocks, but never validate
that the scheduled coroutine actually completes against a real backend.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

import pytest

from axonpush import AsyncAxonPush, EventType
from axonpush.integrations.logging_handler import AxonPushLoggingHandler

pytestmark = pytest.mark.e2e


async def test_logging_handler_with_async_client_round_trip(backend):
    async with AsyncAxonPush(
        api_key=backend.api_key,
        tenant_id=backend.tenant_id,
        base_url=backend.base_url,
    ) as client:
        ch = await client.channels.create(f"async-int-{uuid.uuid4().hex[:8]}", backend.app_id)
        try:
            logger_name = f"e2e.async.{ch.id}"
            logger = logging.getLogger(logger_name)
            logger.handlers.clear()
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            logger.addHandler(AxonPushLoggingHandler(client=client, channel_id=ch.id))
            try:
                logger.error("async round trip")
                # Poll for up to 2s — gives the create_task'd coroutine
                # time to complete its publish.
                events = []
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    events = await client.events.list(ch.id, limit=50)
                    if any(e.payload.get("body") == "async round trip" for e in events):
                        break
                else:
                    pytest.fail(
                        f"async log never reached the backend within 2s; "
                        f"saw events: {[e.payload for e in events]}"
                    )
                matches = [e for e in events if e.payload.get("body") == "async round trip"]
                assert matches[0].event_type == EventType.APP_LOG
                assert matches[0].payload["severityText"] == "ERROR"
            finally:
                logger.handlers.clear()
        finally:
            try:
                await client.channels.delete(ch.id)
            except Exception:
                pass
