import pytest

from axonpush import AxonPush, AsyncAxonPush
from axonpush.resources.events import EventsResource, AsyncEventsResource
from axonpush.resources.channels import ChannelsResource, AsyncChannelsResource
from axonpush.resources.apps import AppsResource, AsyncAppsResource
from axonpush.resources.webhooks import WebhooksResource, AsyncWebhooksResource
from axonpush.resources.traces import TracesResource, AsyncTracesResource

from tests.conftest import API_KEY, TENANT_ID, BASE_URL


class TestSyncClient:
    def test_context_manager(self):
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
            assert client is not None

    def test_exposes_resources(self, client):
        assert isinstance(client.events, EventsResource)
        assert isinstance(client.channels, ChannelsResource)
        assert isinstance(client.apps, AppsResource)
        assert isinstance(client.webhooks, WebhooksResource)
        assert isinstance(client.traces, TracesResource)


class TestAsyncClient:
    async def test_context_manager(self):
        async with AsyncAxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
            assert client is not None

    async def test_exposes_resources(self, async_client):
        assert isinstance(async_client.events, AsyncEventsResource)
        assert isinstance(async_client.channels, AsyncChannelsResource)
        assert isinstance(async_client.apps, AsyncAppsResource)
        assert isinstance(async_client.webhooks, AsyncWebhooksResource)
        assert isinstance(async_client.traces, AsyncTracesResource)
