"""Environments resource — list / create / update / delete / promote."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, cast

from axonpush._internal.api.api.environments import (
    environment_controller_create as _create_op,
    environment_controller_list as _list_op,
    environment_controller_promote as _promote_op,
    environment_controller_remove as _remove_op,
    environment_controller_update as _update_op,
)
from axonpush._internal.api.models import (
    CreateEnvironmentDto,
    EnvironmentControllerPromoteResponse201,
    OkResponseDto,
    UpdateEnvironmentDto,
)
from axonpush._internal.api.types import UNSET
from axonpush.models import Environment

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _build_create_dto(
    *,
    name: str,
    slug: str | None,
    color: str | None,
    is_production: bool | None,
    is_default: bool | None,
    clone_from_env_id: str | None,
) -> CreateEnvironmentDto:
    return CreateEnvironmentDto(
        name=name,
        slug=slug if slug is not None else UNSET,
        color=color if color is not None else UNSET,
        is_production=is_production if is_production is not None else UNSET,
        is_default=is_default if is_default is not None else UNSET,
        clone_from_env_id=clone_from_env_id if clone_from_env_id is not None else UNSET,
    )


def _build_update_dto(
    *,
    name: str | None,
    color: str | None,
    require_confirmation_for_destructive: bool | None,
) -> UpdateEnvironmentDto:
    return UpdateEnvironmentDto(
        name=name if name is not None else UNSET,
        color=color if color is not None else UNSET,
        require_confirmation_for_destructive=(
            require_confirmation_for_destructive
            if require_confirmation_for_destructive is not None
            else UNSET
        ),
    )


class Environments:
    """Synchronous environment management."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def list(self) -> List[Environment] | None:
        """List environments for the caller's organization."""
        return self._client._invoke(_list_op)

    def create(
        self,
        name: str,
        *,
        slug: str | None = None,
        color: str | None = None,
        is_production: bool | None = None,
        is_default: bool | None = None,
        clone_from_env_id: str | None = None,
    ) -> Environment | None:
        """Create an environment.

        Args:
            name: Human-readable name.
            slug: Stable slug used in API headers / SDK config.
            color: Optional UI tag colour (hex).
            is_production: Mark as production-class.
            is_default: Make this the default for un-tagged calls.
            clone_from_env_id: Optional source env to copy resources from.
        """
        body = _build_create_dto(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
            clone_from_env_id=clone_from_env_id,
        )
        return self._client._invoke(_create_op, body=body)

    def update(
        self,
        env_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        require_confirmation_for_destructive: bool | None = None,
    ) -> Environment | None:
        """Edit a mutable subset of environment fields."""
        body = _build_update_dto(
            name=name,
            color=color,
            require_confirmation_for_destructive=require_confirmation_for_destructive,
        )
        return self._client._invoke(_update_op, id=env_id, body=body)

    def delete(self, env_id: str) -> OkResponseDto | None:
        """Soft-delete an environment."""
        return self._client._invoke(_remove_op, id=env_id)

    def promote_to_default(
        self, env_id: str
    ) -> EnvironmentControllerPromoteResponse201 | Environment | None:
        """Promote an environment to be the org-wide default."""
        # Generated op has a union return type that confuses TypeVar inference.
        return cast(
            "EnvironmentControllerPromoteResponse201 | Environment | None",
            self._client._invoke(_promote_op, id=env_id),
        )


class AsyncEnvironments:
    """Async sibling of :class:`Environments`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def list(self) -> List[Environment] | None:
        """See :meth:`Environments.list`."""
        return await self._client._invoke(_list_op)

    async def create(
        self,
        name: str,
        *,
        slug: str | None = None,
        color: str | None = None,
        is_production: bool | None = None,
        is_default: bool | None = None,
        clone_from_env_id: str | None = None,
    ) -> Environment | None:
        """See :meth:`Environments.create`."""
        body = _build_create_dto(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
            clone_from_env_id=clone_from_env_id,
        )
        return await self._client._invoke(_create_op, body=body)

    async def update(
        self,
        env_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        require_confirmation_for_destructive: bool | None = None,
    ) -> Environment | None:
        """See :meth:`Environments.update`."""
        body = _build_update_dto(
            name=name,
            color=color,
            require_confirmation_for_destructive=require_confirmation_for_destructive,
        )
        return await self._client._invoke(_update_op, id=env_id, body=body)

    async def delete(self, env_id: str) -> OkResponseDto | None:
        """See :meth:`Environments.delete`."""
        return await self._client._invoke(_remove_op, id=env_id)

    async def promote_to_default(
        self, env_id: str
    ) -> EnvironmentControllerPromoteResponse201 | Environment | None:
        """See :meth:`Environments.promote_to_default`."""
        return cast(
            "EnvironmentControllerPromoteResponse201 | Environment | None",
            await self._client._invoke(_promote_op, id=env_id),
        )
