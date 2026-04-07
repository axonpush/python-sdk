from __future__ import annotations

from typing import List, Optional

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open
from axonpush.models.apps import App, CreateAppParams


class AppsResource:
    """Synchronous resource for app CRUD."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(self, name: str) -> Optional[App]:
        """Create a new app (POST /apps)."""
        body = CreateAppParams(name=name)
        data = self._transport.request(
            "POST", "/apps", json=body.model_dump(exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    def get(self, app_id: int) -> Optional[App]:
        """Get an app by ID (GET /apps/:id)."""
        data = self._transport.request("GET", f"/apps/{app_id}")
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    def list(self) -> List[App]:
        """List all apps (GET /apps)."""
        data = self._transport.request("GET", "/apps")
        if _is_fail_open(data):
            return []
        return [App.model_validate(a) for a in data]

    def update(self, app_id: int, name: str) -> Optional[App]:
        """Update an app (PATCH /apps/:id)."""
        data = self._transport.request("PATCH", f"/apps/{app_id}", json={"name": name})
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    def delete(self, app_id: int) -> None:
        """Delete an app (DELETE /apps/:id)."""
        self._transport.request("DELETE", f"/apps/{app_id}")


class AsyncAppsResource:
    """Asynchronous resource for app CRUD."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(self, name: str) -> Optional[App]:
        body = CreateAppParams(name=name)
        data = await self._transport.request(
            "POST", "/apps", json=body.model_dump(exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    async def get(self, app_id: int) -> Optional[App]:
        data = await self._transport.request("GET", f"/apps/{app_id}")
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    async def list(self) -> List[App]:
        data = await self._transport.request("GET", "/apps")
        if _is_fail_open(data):
            return []
        return [App.model_validate(a) for a in data]

    async def update(self, app_id: int, name: str) -> Optional[App]:
        data = await self._transport.request("PATCH", f"/apps/{app_id}", json={"name": name})
        if _is_fail_open(data):
            return None
        return App.model_validate(data)

    async def delete(self, app_id: int) -> None:
        await self._transport.request("DELETE", f"/apps/{app_id}")
