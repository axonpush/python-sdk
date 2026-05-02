"""Channels resource — CRUD over channels within an app."""

from __future__ import annotations

from typing import TYPE_CHECKING

from axonpush._internal.api.api.channels import (
    channel_controller_create_channel as _create_op,
    channel_controller_delete_channel as _delete_op,
    channel_controller_get_channel as _get_op,
    channel_controller_update_channel as _update_op,
)
from axonpush._internal.api.models import CreateChannelDto, OkResponseDto
from axonpush.models import Channel

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _build_create_dto(*, name: str, app_id: str) -> CreateChannelDto:
    return CreateChannelDto(name=name, app_id=app_id)


class Channels:
    """Synchronous channel CRUD."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def get(self, channel_id: str) -> Channel | None:
        """Fetch a single channel by UUID.

        Args:
            channel_id: UUID of the channel.

        Returns:
            The :class:`Channel`, or ``None`` on fail-open.
        """
        return self._client._invoke(_get_op, id=channel_id)

    def create(self, name: str, app_id: str) -> Channel | None:
        """Create a channel inside an app.

        Args:
            name: Human-readable channel name.
            app_id: UUID of the parent app.

        Returns:
            The created :class:`Channel`, or ``None`` on fail-open.
        """
        return self._client._invoke(
            _create_op, body=_build_create_dto(name=name, app_id=app_id)
        )

    def update(self, channel_id: str) -> OkResponseDto | None:
        """Touch / re-validate a channel.

        The backend currently exposes ``PUT /channel/:id`` without a body.
        See ``channel_controller_update_channel`` in the generated layer.
        """
        return self._client._invoke(_update_op, id=channel_id)

    def delete(self, channel_id: str) -> OkResponseDto | None:
        """Soft-delete a channel."""
        return self._client._invoke(_delete_op, id=channel_id)


class AsyncChannels:
    """Async sibling of :class:`Channels`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def get(self, channel_id: str) -> Channel | None:
        """See :meth:`Channels.get`."""
        return await self._client._invoke(_get_op, id=channel_id)

    async def create(self, name: str, app_id: str) -> Channel | None:
        """See :meth:`Channels.create`."""
        return await self._client._invoke(
            _create_op, body=_build_create_dto(name=name, app_id=app_id)
        )

    async def update(self, channel_id: str) -> OkResponseDto | None:
        """See :meth:`Channels.update`."""
        return await self._client._invoke(_update_op, id=channel_id)

    async def delete(self, channel_id: str) -> OkResponseDto | None:
        """See :meth:`Channels.delete`."""
        return await self._client._invoke(_delete_op, id=channel_id)
