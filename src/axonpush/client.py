from __future__ import annotations

from axonpush._auth import AuthConfig
from axonpush._http import AsyncTransport, SyncTransport
from axonpush.realtime.websocket import AsyncWebSocketClient, WebSocketClient
from axonpush.resources.apps import AppsResource, AsyncAppsResource
from axonpush.resources.channels import AsyncChannelsResource, ChannelsResource
from axonpush.resources.events import AsyncEventsResource, EventsResource
from axonpush.resources.traces import AsyncTracesResource, TracesResource
from axonpush.resources.webhooks import AsyncWebhooksResource, WebhooksResource


class AxonPush:
    """Synchronous AxonPush client. Thread-safe.

    Usage::

        with AxonPush(api_key="ak_...", tenant_id="1") as client:
            event = client.events.publish(
                "web_search", {"query": "AI agents"}, channel_id=1,
                agent_id="researcher", event_type="agent.tool_call.start",
            )
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        *,
        base_url: str = "https://api.axonpush.com",
        timeout: float = 30.0,
    ) -> None:
        self._auth = AuthConfig(api_key, tenant_id, base_url)
        self._transport = SyncTransport(self._auth, timeout)

        self.events = EventsResource(self._transport)
        self.channels = ChannelsResource(self._transport)
        self.apps = AppsResource(self._transport)
        self.webhooks = WebhooksResource(self._transport)
        self.traces = TracesResource(self._transport)

    def connect_websocket(self) -> WebSocketClient:
        """Create and connect a Socket.IO WebSocket client."""
        ws = WebSocketClient(self._auth)
        ws.connect()
        return ws

    def close(self) -> None:
        """Close the underlying HTTP transport."""
        self._transport.close()

    def __enter__(self) -> AxonPush:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncAxonPush:
    """Asynchronous AxonPush client. Task-safe.

    Usage::

        async with AsyncAxonPush(api_key="ak_...", tenant_id="1") as client:
            event = await client.events.publish(
                "web_search", {"query": "AI agents"}, channel_id=1,
                agent_id="researcher", event_type="agent.tool_call.start",
            )
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        *,
        base_url: str = "https://api.axonpush.com",
        timeout: float = 30.0,
    ) -> None:
        self._auth = AuthConfig(api_key, tenant_id, base_url)
        self._transport = AsyncTransport(self._auth, timeout)

        self.events = AsyncEventsResource(self._transport)
        self.channels = AsyncChannelsResource(self._transport)
        self.apps = AsyncAppsResource(self._transport)
        self.webhooks = AsyncWebhooksResource(self._transport)
        self.traces = AsyncTracesResource(self._transport)

    async def connect_websocket(self) -> AsyncWebSocketClient:
        """Create and connect an async Socket.IO WebSocket client."""
        ws = AsyncWebSocketClient(self._auth)
        await ws.connect()
        return ws

    async def close(self) -> None:
        """Close the underlying HTTP transport."""
        await self._transport.close()

    async def __aenter__(self) -> AsyncAxonPush:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
