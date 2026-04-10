"""Unit tests for the AxonPush client surface — no backend required."""
from __future__ import annotations

import httpx

from axonpush import AsyncAxonPush, AxonPush
from axonpush.resources.apps import AppsResource, AsyncAppsResource
from axonpush.resources.channels import AsyncChannelsResource, ChannelsResource
from axonpush.resources.events import AsyncEventsResource, EventsResource
from axonpush.resources.traces import AsyncTracesResource, TracesResource
from axonpush.resources.webhooks import AsyncWebhooksResource, WebhooksResource

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


class TestSyncClient:
    def test_construction(self):
        c = AxonPush(api_key="ak_x", tenant_id="42", base_url="http://localhost:3000")
        assert c is not None
        c.close()

    def test_context_manager_closes_transport(self):
        with AxonPush(api_key="ak_x", tenant_id="42", base_url=BASE_URL) as c:
            assert c is not None

    def test_exposes_resources(self):
        c = AxonPush(api_key="ak_x", tenant_id="42", base_url=BASE_URL)
        assert isinstance(c.events, EventsResource)
        assert isinstance(c.channels, ChannelsResource)
        assert isinstance(c.apps, AppsResource)
        assert isinstance(c.webhooks, WebhooksResource)
        assert isinstance(c.traces, TracesResource)
        c.close()

    def test_auth_headers_sent_on_request(self, mock_router):
        """Verify auth headers reach the wire by inspecting the captured
        request, not the SDK's internal _transport state."""
        route = mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "identifier": "x",
                    "payload": {},
                    "eventType": "custom",
                },
            )
        )
        with AxonPush(api_key="ak_secret", tenant_id="99", base_url=BASE_URL) as c:
            c.events.publish("x", {}, channel_id=1)

        sent = route.calls.last.request.headers
        assert sent["x-api-key"] == "ak_secret"
        assert sent["x-tenant-id"] == "99"
        assert sent["content-type"] == "application/json"

    def test_timeout_passed_to_httpx(self):
        """Verify the ``timeout`` constructor arg flows into the underlying
        httpx.Client. (Issue #15 — previously untested.)"""
        c = AxonPush(
            api_key="ak_x",
            tenant_id="1",
            base_url=BASE_URL,
            timeout=12.5,
        )
        # httpx.Client stores a Timeout object on its private _timeout attr
        assert c._transport._client.timeout.read == 12.5
        # Connect timeout is hardcoded to 5.0 in _http.py
        assert c._transport._client.timeout.connect == 5.0
        c.close()

    def test_base_url_trailing_slash_stripped(self):
        c = AxonPush(api_key="ak_x", tenant_id="1", base_url="http://localhost:3000/")
        assert c._auth.base_url == "http://localhost:3000"
        c.close()

    def test_fail_open_defaults_to_true(self):
        c = AxonPush(api_key="ak_x", tenant_id="1", base_url=BASE_URL)
        assert c._fail_open is True
        c.close()

    def test_publish_succeeds_with_mocked_backend(self, mock_router):
        mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "identifier": "test",
                    "payload": {"k": "v"},
                    "eventType": "agent.start",
                },
            )
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            event = c.events.publish("test", {"k": "v"}, channel_id=5)
        assert event is not None
        assert event.id == 123
        assert event.identifier == "test"


class TestAsyncClient:
    async def test_construction(self):
        c = AsyncAxonPush(api_key="ak_x", tenant_id="42", base_url=BASE_URL)
        assert c is not None
        await c.close()

    async def test_context_manager_closes_transport(self):
        async with AsyncAxonPush(api_key="ak_x", tenant_id="42", base_url=BASE_URL) as c:
            assert c is not None

    async def test_exposes_resources(self):
        c = AsyncAxonPush(api_key="ak_x", tenant_id="42", base_url=BASE_URL)
        assert isinstance(c.events, AsyncEventsResource)
        assert isinstance(c.channels, AsyncChannelsResource)
        assert isinstance(c.apps, AsyncAppsResource)
        assert isinstance(c.webhooks, AsyncWebhooksResource)
        assert isinstance(c.traces, AsyncTracesResource)
        await c.close()

    async def test_publish_succeeds_with_mocked_backend(self, mock_router):
        mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "identifier": "async_test",
                    "payload": {},
                    "eventType": "custom",
                },
            )
        )
        async with AsyncAxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            event = await c.events.publish("async_test", {}, channel_id=7)
        assert event is not None
        assert event.identifier == "async_test"
