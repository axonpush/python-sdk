"""Apps resource — CRUD over applications inside an organization."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from axonpush._internal.api.api.apps import (
    apps_controller_create_app as _create_op,
    apps_controller_delete_app as _delete_op,
    apps_controller_edit_app as _edit_op,
    apps_controller_get_all_apps as _list_op,
    apps_controller_get_app as _get_op,
)
from axonpush._internal.api.models import CreateAppDto, OkResponseDto
from axonpush.models import App

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


class Apps:
    """Synchronous app CRUD."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def list(self) -> List[App] | None:
        """List all apps the caller's API key can see.

        Returns:
            A list of :class:`App`, or ``None`` on fail-open.
        """
        return self._client._invoke(_list_op)

    def get(self, app_id: str) -> App | None:
        """Fetch an app by UUID.

        Args:
            app_id: UUID of the app.
        """
        return self._client._invoke(_get_op, id=app_id)

    def create(self, name: str) -> App | None:
        """Create an app under the calling org.

        Args:
            name: Human-readable app name.
        """
        return self._client._invoke(_create_op, body=CreateAppDto(name=name))

    def update(self, app_id: str, *, name: str) -> OkResponseDto | None:
        """Edit an app's name.

        Args:
            app_id: UUID of the app to edit.
            name: New name.
        """
        return self._client._invoke(_edit_op, id=app_id, body=CreateAppDto(name=name))

    def delete(self, app_id: str) -> OkResponseDto | None:
        """Soft-delete an app."""
        return self._client._invoke(_delete_op, id=app_id)


class AsyncApps:
    """Async sibling of :class:`Apps`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def list(self) -> List[App] | None:
        """See :meth:`Apps.list`."""
        return await self._client._invoke(_list_op)

    async def get(self, app_id: str) -> App | None:
        """See :meth:`Apps.get`."""
        return await self._client._invoke(_get_op, id=app_id)

    async def create(self, name: str) -> App | None:
        """See :meth:`Apps.create`."""
        return await self._client._invoke(_create_op, body=CreateAppDto(name=name))

    async def update(self, app_id: str, *, name: str) -> OkResponseDto | None:
        """See :meth:`Apps.update`."""
        return await self._client._invoke(_edit_op, id=app_id, body=CreateAppDto(name=name))

    async def delete(self, app_id: str) -> OkResponseDto | None:
        """See :meth:`Apps.delete`."""
        return await self._client._invoke(_delete_op, id=app_id)
