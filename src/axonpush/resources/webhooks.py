from __future__ import annotations

from typing import List, Optional

from axonpush._http import AsyncTransport, SyncTransport
from axonpush.models.webhooks import (
    CreateWebhookEndpointParams,
    WebhookDelivery,
    WebhookEndpoint,
)


class WebhooksResource:
    """Synchronous resource for webhook endpoint management."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create_endpoint(
        self,
        url: str,
        channel_id: int,
        *,
        secret: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> WebhookEndpoint:
        """Create a webhook endpoint (POST /webhooks/endpoints)."""
        body = CreateWebhookEndpointParams(
            url=url,
            channel_id=channel_id,
            secret=secret,
            event_types=event_types,
            description=description,
        )
        data = self._transport.request(
            "POST",
            "/webhooks/endpoints",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        return WebhookEndpoint.model_validate(data)

    def list_endpoints(self, channel_id: int) -> List[WebhookEndpoint]:
        """List webhook endpoints for a channel (GET /webhooks/endpoints/channel/:channelId)."""
        data = self._transport.request("GET", f"/webhooks/endpoints/channel/{channel_id}")
        return [WebhookEndpoint.model_validate(e) for e in data]

    def delete_endpoint(self, endpoint_id: int) -> None:
        """Deactivate a webhook endpoint (DELETE /webhooks/endpoints/:id)."""
        self._transport.request("DELETE", f"/webhooks/endpoints/{endpoint_id}")

    def get_deliveries(self, endpoint_id: int) -> List[WebhookDelivery]:
        """Get delivery logs for an endpoint (GET /webhooks/deliveries/:endpointId)."""
        data = self._transport.request("GET", f"/webhooks/deliveries/{endpoint_id}")
        return [WebhookDelivery.model_validate(d) for d in data]


class AsyncWebhooksResource:
    """Asynchronous resource for webhook endpoint management."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create_endpoint(
        self,
        url: str,
        channel_id: int,
        *,
        secret: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> WebhookEndpoint:
        body = CreateWebhookEndpointParams(
            url=url,
            channel_id=channel_id,
            secret=secret,
            event_types=event_types,
            description=description,
        )
        data = await self._transport.request(
            "POST",
            "/webhooks/endpoints",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        return WebhookEndpoint.model_validate(data)

    async def list_endpoints(self, channel_id: int) -> List[WebhookEndpoint]:
        data = await self._transport.request("GET", f"/webhooks/endpoints/channel/{channel_id}")
        return [WebhookEndpoint.model_validate(e) for e in data]

    async def delete_endpoint(self, endpoint_id: int) -> None:
        await self._transport.request("DELETE", f"/webhooks/endpoints/{endpoint_id}")

    async def get_deliveries(self, endpoint_id: int) -> List[WebhookDelivery]:
        data = await self._transport.request("GET", f"/webhooks/deliveries/{endpoint_id}")
        return [WebhookDelivery.model_validate(d) for d in data]
