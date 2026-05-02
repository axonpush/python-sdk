"""Webhooks resource — manage endpoints and inspect deliveries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from axonpush._internal.api.api.webhooks import (
    webhook_controller_create_endpoint as _create_op,
    webhook_controller_delete_endpoint as _delete_op,
    webhook_controller_get_deliveries as _deliveries_op,
    webhook_controller_list_endpoints as _list_op,
)
from axonpush._internal.api.models import (
    CreateWebhookEndpointDto,
    MessageResponseDto,
)
from axonpush._internal.api.types import UNSET
from axonpush.models import (
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointCreateResponseDto,
)

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _build_create_dto(
    *,
    url: str,
    channel_id: str,
    secret: str | None,
    event_types: list[str] | None,
    description: str | None,
) -> CreateWebhookEndpointDto:
    return CreateWebhookEndpointDto(
        url=url,
        channel_id=channel_id,
        secret=secret if secret is not None else UNSET,
        event_types=event_types if event_types is not None else UNSET,
        description=description if description is not None else UNSET,
    )


class Webhooks:
    """Synchronous webhook endpoint + delivery operations."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def create_endpoint(
        self,
        *,
        url: str,
        channel_id: str,
        secret: str | None = None,
        event_types: list[str] | None = None,
        description: str | None = None,
    ) -> WebhookEndpointCreateResponseDto | None:
        """Register a webhook endpoint on a channel.

        Args:
            url: Target URL the backend will POST to.
            channel_id: Source channel UUID.
            secret: Optional signing secret. Server-generated if omitted.
            event_types: Optional event-type filter (e.g. ``["agent.start"]``).
            description: Free-form note.

        Returns:
            The created endpoint (response includes the raw secret once).
        """
        body = _build_create_dto(
            url=url,
            channel_id=channel_id,
            secret=secret,
            event_types=event_types,
            description=description,
        )
        return self._client._invoke(_create_op.sync, body=body)

    def list_endpoints(self, channel_id: str) -> list[WebhookEndpoint] | None:
        """List endpoints attached to a channel."""
        return self._client._invoke(_list_op.sync, channel_id=channel_id)

    def delete_endpoint(self, endpoint_id: str) -> MessageResponseDto | None:
        """Delete a webhook endpoint."""
        return self._client._invoke(_delete_op.sync, id=endpoint_id)

    def deliveries(self, endpoint_id: str) -> list[WebhookDelivery] | None:
        """List deliveries for a webhook endpoint."""
        return self._client._invoke(_deliveries_op.sync, endpoint_id=endpoint_id)


class AsyncWebhooks:
    """Async sibling of :class:`Webhooks`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def create_endpoint(
        self,
        *,
        url: str,
        channel_id: str,
        secret: str | None = None,
        event_types: list[str] | None = None,
        description: str | None = None,
    ) -> WebhookEndpointCreateResponseDto | None:
        """See :meth:`Webhooks.create_endpoint`."""
        body = _build_create_dto(
            url=url,
            channel_id=channel_id,
            secret=secret,
            event_types=event_types,
            description=description,
        )
        return await self._client._invoke(_create_op.asyncio, body=body)

    async def list_endpoints(self, channel_id: str) -> list[WebhookEndpoint] | None:
        """See :meth:`Webhooks.list_endpoints`."""
        return await self._client._invoke(_list_op.asyncio, channel_id=channel_id)

    async def delete_endpoint(self, endpoint_id: str) -> MessageResponseDto | None:
        """See :meth:`Webhooks.delete_endpoint`."""
        return await self._client._invoke(_delete_op.asyncio, id=endpoint_id)

    async def deliveries(self, endpoint_id: str) -> list[WebhookDelivery] | None:
        """See :meth:`Webhooks.deliveries`."""
        return await self._client._invoke(_deliveries_op.asyncio, endpoint_id=endpoint_id)
