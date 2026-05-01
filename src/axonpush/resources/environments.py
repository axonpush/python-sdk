from __future__ import annotations

from typing import List, Optional

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open
from axonpush.models.environments import (
    CreateEnvironmentParams,
    Environment,
    UpdateEnvironmentParams,
)


class EnvironmentsResource:
    """Synchronous resource for org-level environment CRUD."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self) -> List[Environment]:
        """List all environments for the org (GET /environments)."""
        data = self._transport.request("GET", "/environments")
        if _is_fail_open(data):
            return []
        return [Environment.model_validate(e) for e in data]

    def create(
        self,
        name: str,
        *,
        slug: Optional[str] = None,
        color: Optional[str] = None,
        is_production: bool = False,
        is_default: bool = False,
        clone_from_env_id: Optional[str] = None,
    ) -> Optional[Environment]:
        """Create an environment (POST /environments)."""
        body = CreateEnvironmentParams(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
            clone_from_env_id=clone_from_env_id,
        )
        data = self._transport.request(
            "POST",
            "/environments",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)

    def update(
        self,
        env_id: str,
        *,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        color: Optional[str] = None,
        is_production: Optional[bool] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[Environment]:
        """Update an environment (PATCH /environments/:id)."""
        body = UpdateEnvironmentParams(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
        )
        data = self._transport.request(
            "PATCH",
            f"/environments/{env_id}",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)

    def delete(self, env_id: str) -> None:
        """Delete an environment (DELETE /environments/:id)."""
        self._transport.request("DELETE", f"/environments/{env_id}")

    def promote_to_default(self, env_id: str) -> Optional[Environment]:
        """Promote an environment to org default (POST /environments/:id/promote-to-default)."""
        data = self._transport.request(
            "POST", f"/environments/{env_id}/promote-to-default"
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)


class AsyncEnvironmentsResource:
    """Asynchronous resource for org-level environment CRUD."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self) -> List[Environment]:
        data = await self._transport.request("GET", "/environments")
        if _is_fail_open(data):
            return []
        return [Environment.model_validate(e) for e in data]

    async def create(
        self,
        name: str,
        *,
        slug: Optional[str] = None,
        color: Optional[str] = None,
        is_production: bool = False,
        is_default: bool = False,
        clone_from_env_id: Optional[str] = None,
    ) -> Optional[Environment]:
        body = CreateEnvironmentParams(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
            clone_from_env_id=clone_from_env_id,
        )
        data = await self._transport.request(
            "POST",
            "/environments",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)

    async def update(
        self,
        env_id: str,
        *,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        color: Optional[str] = None,
        is_production: Optional[bool] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[Environment]:
        body = UpdateEnvironmentParams(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
        )
        data = await self._transport.request(
            "PATCH",
            f"/environments/{env_id}",
            json=body.model_dump(by_alias=True, exclude_none=True),
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)

    async def delete(self, env_id: str) -> None:
        await self._transport.request("DELETE", f"/environments/{env_id}")

    async def promote_to_default(self, env_id: str) -> Optional[Environment]:
        data = await self._transport.request(
            "POST", f"/environments/{env_id}/promote-to-default"
        )
        if _is_fail_open(data):
            return None
        return Environment.model_validate(data)
