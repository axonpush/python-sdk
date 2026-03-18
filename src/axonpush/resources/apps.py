from __future__ import annotations

from typing import List

from axonpush._http import AsyncTransport, SyncTransport
from axonpush.models.apps import App, CreateAppParams


class AppsResource:
    """Synchronous resource for app CRUD."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(self, name: str) -> App:
        """Create a new app (POST /apps)."""
        body = CreateAppParams(name=name)
        data = self._transport.request(
            "POST", "/apps", json=body.model_dump(exclude_none=True)
        )
        return App.model_validate(data)

    def get(self, app_id: int) -> App:
        """Get an app by ID (GET /apps/:id)."""
        data = self._transport.request("GET", f"/apps/{app_id}")
        return App.model_validate(data)

    def list(self) -> List[App]:
        """List all apps (GET /apps)."""
        data = self._transport.request("GET", "/apps")
        return [App.model_validate(a) for a in data]

    def update(self, app_id: int, name: str) -> App:
        """Update an app (PATCH /apps/:id)."""
        data = self._transport.request("PATCH", f"/apps/{app_id}", json={"name": name})
        return App.model_validate(data)

    def delete(self, app_id: int) -> None:
        """Delete an app (DELETE /apps/:id)."""
        self._transport.request("DELETE", f"/apps/{app_id}")


class AsyncAppsResource:
    """Asynchronous resource for app CRUD."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(self, name: str) -> App:
        body = CreateAppParams(name=name)
        data = await self._transport.request(
            "POST", "/apps", json=body.model_dump(exclude_none=True)
        )
        return App.model_validate(data)

    async def get(self, app_id: int) -> App:
        data = await self._transport.request("GET", f"/apps/{app_id}")
        return App.model_validate(data)

    async def list(self) -> List[App]:
        data = await self._transport.request("GET", "/apps")
        return [App.model_validate(a) for a in data]

    async def update(self, app_id: int, name: str) -> App:
        data = await self._transport.request("PATCH", f"/apps/{app_id}", json={"name": name})
        return App.model_validate(data)

    async def delete(self, app_id: int) -> None:
        await self._transport.request("DELETE", f"/apps/{app_id}")
