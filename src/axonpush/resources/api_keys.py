"""API keys resource — create, list, revoke."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from axonpush._internal.api.api.api_keys import (
    api_key_controller_create_api_key as _create_op,
    api_key_controller_list_api_keys as _list_op,
    api_key_controller_revoke_api_key as _revoke_op,
)
from axonpush._internal.api.models import (
    CreateApiKeyDto,
    CreateApiKeyDtoScopesItem,
    MessageResponseDto,
)
from axonpush._internal.api.types import UNSET
from axonpush.models import ApiKey, ApiKeyCreateResponseDto

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _coerce_scopes(
    scopes: List[CreateApiKeyDtoScopesItem | str] | None,
) -> List[CreateApiKeyDtoScopesItem] | object:
    if scopes is None:
        return UNSET
    return [
        s if isinstance(s, CreateApiKeyDtoScopesItem) else CreateApiKeyDtoScopesItem(s)
        for s in scopes
    ]


def _build_create_dto(
    *,
    name: str,
    organization_id: str,
    scopes: List[CreateApiKeyDtoScopesItem | str] | None,
    app_id: str | None,
    environment_id: str | None,
    allow_environment_override: bool | None,
) -> CreateApiKeyDto:
    return CreateApiKeyDto(
        name=name,
        organization_id=organization_id,
        scopes=_coerce_scopes(scopes),  # type: ignore[arg-type]  # generated UNSET sentinel
        app_id=app_id if app_id is not None else UNSET,
        environment_id=environment_id if environment_id is not None else UNSET,
        allow_environment_override=(
            allow_environment_override if allow_environment_override is not None else UNSET
        ),
    )


class ApiKeys:
    """Synchronous API key management."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def list(self) -> List[ApiKey] | None:
        """List API keys for the calling org."""
        return self._client._invoke(_list_op)

    def create(
        self,
        name: str,
        *,
        organization_id: str,
        scopes: List[CreateApiKeyDtoScopesItem | str] | None = None,
        app_id: str | None = None,
        environment_id: str | None = None,
        allow_environment_override: bool | None = None,
    ) -> ApiKeyCreateResponseDto | None:
        """Create an API key.

        Args:
            name: Human-readable label.
            organization_id: Org UUID this key belongs to.
            scopes: Optional list of scope strings/enums.
            app_id: Optional restriction to a single app.
            environment_id: Optional restriction to a single environment.
            allow_environment_override: Permit per-call ``environment`` overrides.

        Returns:
            The created key, including the raw ``key`` value (returned once).
        """
        body = _build_create_dto(
            name=name,
            organization_id=organization_id,
            scopes=scopes,
            app_id=app_id,
            environment_id=environment_id,
            allow_environment_override=allow_environment_override,
        )
        return self._client._invoke(_create_op, body=body)

    def delete(self, key_id: str) -> MessageResponseDto | None:
        """Revoke an API key by UUID."""
        return self._client._invoke(_revoke_op, id=key_id)


class AsyncApiKeys:
    """Async sibling of :class:`ApiKeys`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def list(self) -> List[ApiKey] | None:
        """See :meth:`ApiKeys.list`."""
        return await self._client._invoke(_list_op)

    async def create(
        self,
        name: str,
        *,
        organization_id: str,
        scopes: List[CreateApiKeyDtoScopesItem | str] | None = None,
        app_id: str | None = None,
        environment_id: str | None = None,
        allow_environment_override: bool | None = None,
    ) -> ApiKeyCreateResponseDto | None:
        """See :meth:`ApiKeys.create`."""
        body = _build_create_dto(
            name=name,
            organization_id=organization_id,
            scopes=scopes,
            app_id=app_id,
            environment_id=environment_id,
            allow_environment_override=allow_environment_override,
        )
        return await self._client._invoke(_create_op, body=body)

    async def delete(self, key_id: str) -> MessageResponseDto | None:
        """See :meth:`ApiKeys.delete`."""
        return await self._client._invoke(_revoke_op, id=key_id)
