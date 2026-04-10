import uuid

import pytest

from axonpush import EventType
from axonpush.models.apps import App
from axonpush.models.channels import Channel
from axonpush.models.events import Event

from tests.conftest import EXISTING_APP_ID

pytestmark = pytest.mark.e2e


class TestAsyncEvents:
    async def test_publish_event(self, async_client):
        ch = await async_client.channels.create(f"async-ch-{uuid.uuid4().hex[:8]}", EXISTING_APP_ID)

        event = await async_client.events.publish(
            "async_action",
            {"key": "value"},
            channel_id=ch.id,
            agent_id="async-agent",
            event_type=EventType.AGENT_TOOL_CALL_START,
        )
        assert isinstance(event, Event)
        assert event.identifier == "async_action"
        assert event.agent_id == "async-agent"

        try:
            await async_client.channels.delete(ch.id)
        except Exception:
            pass

    async def test_list_events(self, async_client):
        ch = await async_client.channels.create(f"async-ch-{uuid.uuid4().hex[:8]}", EXISTING_APP_ID)

        await async_client.events.publish(
            "async_list_1", {"i": 1}, channel_id=ch.id
        )

        events = await async_client.events.list(ch.id)
        assert isinstance(events, list)
        assert all(isinstance(e, Event) for e in events)

        try:
            await async_client.channels.delete(ch.id)
        except Exception:
            pass


class TestAsyncApps:
    async def test_get_app(self, async_client):
        app = await async_client.apps.get(EXISTING_APP_ID)
        assert isinstance(app, App)
        assert app.id == EXISTING_APP_ID


class TestAsyncChannels:
    async def test_crud(self, async_client):
        name = f"async-ch-{uuid.uuid4().hex[:8]}"
        ch = await async_client.channels.create(name, EXISTING_APP_ID)
        assert isinstance(ch, Channel)
        assert ch.name == name

        fetched = await async_client.channels.get(ch.id)
        assert fetched.id == ch.id

        try:
            await async_client.channels.delete(ch.id)
        except Exception:
            pass
