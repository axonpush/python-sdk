"""Organizations resource — CRUD, invitations, member admin."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from axonpush._internal.api.api.organizations import (
    organization_controller_create_invitation as _invite_op,
    organization_controller_create_organization as _create_op,
    organization_controller_delete_invitation as _delete_invite_op,
    organization_controller_delete_organization as _delete_op,
    organization_controller_edit_organization as _edit_op,
    organization_controller_get_all_organizations as _list_op,
    organization_controller_get_organization as _get_op,
    organization_controller_remove_member as _remove_member_op,
    organization_controller_transfer_ownership as _transfer_op,
)
from axonpush._internal.api.models import (
    CreateInvitationDto,
    CreateInvitationDtoDesiredRole,
    CreateOrganizationDto,
    OkResponseDto,
    SuccessResponseDto,
    TransferOwnershipDto,
)
from axonpush._internal.api.models.invitation_response_dto import InvitationResponseDto
from axonpush._internal.api.types import UNSET
from axonpush.models import Organization, OrganizationCreateResponseDto

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _build_create_dto(*, name: str, slug: str, description: str | None) -> CreateOrganizationDto:
    return CreateOrganizationDto(
        name=name,
        slug=slug,
        description=description if description is not None else UNSET,
    )


def _build_invite_dto(
    *, email: str, role: CreateInvitationDtoDesiredRole | str
) -> CreateInvitationDto:
    desired_role = (
        role
        if isinstance(role, CreateInvitationDtoDesiredRole)
        else CreateInvitationDtoDesiredRole(role)
    )
    return CreateInvitationDto(invited_email=email, desired_role=desired_role)


class Organizations:
    """Synchronous organization management."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def list(self) -> List[Organization] | None:
        """List organizations the caller is a member of."""
        return self._client._invoke(_list_op.sync)

    def get(self, org_id: str) -> Organization | None:
        """Fetch a single organization by UUID."""
        return self._client._invoke(_get_op.sync, id=org_id)

    def create(
        self, name: str, *, slug: str, description: str | None = None
    ) -> OrganizationCreateResponseDto | None:
        """Create a new organization (returns initial access tokens)."""
        return self._client._invoke(
            _create_op.sync,
            body=_build_create_dto(name=name, slug=slug, description=description),
        )

    def update(
        self,
        org_id: str,
        *,
        name: str,
        slug: str,
        description: str | None = None,
    ) -> OkResponseDto | None:
        """Edit organization name / slug / description."""
        return self._client._invoke(
            _edit_op.sync,
            id=org_id,
            body=_build_create_dto(name=name, slug=slug, description=description),
        )

    def delete(self, org_id: str) -> OkResponseDto | None:
        """Soft-delete an organization."""
        return self._client._invoke(_delete_op.sync, id=org_id)

    def invite(
        self,
        org_id: str,
        email: str,
        *,
        role: CreateInvitationDtoDesiredRole | str = CreateInvitationDtoDesiredRole.USER,
    ) -> InvitationResponseDto | None:
        """Invite a user to an organization."""
        return self._client._invoke(
            _invite_op.sync, id=org_id, body=_build_invite_dto(email=email, role=role)
        )

    def cancel_invitation(self, org_id: str, invitation_id: str) -> SuccessResponseDto | None:
        """Cancel a pending invitation."""
        return self._client._invoke(_delete_invite_op.sync, id=org_id, invitation_id=invitation_id)

    def remove_member(self, org_id: str, user_id: str) -> SuccessResponseDto | None:
        """Remove a member from an organization."""
        return self._client._invoke(_remove_member_op.sync, id=org_id, user_id=user_id)

    def transfer_ownership(self, org_id: str, target_user_id: str) -> SuccessResponseDto | None:
        """Transfer organization ownership to another member."""
        return self._client._invoke(
            _transfer_op.sync,
            id=org_id,
            body=TransferOwnershipDto(user_id=target_user_id),
        )


class AsyncOrganizations:
    """Async sibling of :class:`Organizations`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def list(self) -> List[Organization] | None:
        """See :meth:`Organizations.list`."""
        return await self._client._invoke(_list_op.asyncio)

    async def get(self, org_id: str) -> Organization | None:
        """See :meth:`Organizations.get`."""
        return await self._client._invoke(_get_op.asyncio, id=org_id)

    async def create(
        self, name: str, *, slug: str, description: str | None = None
    ) -> OrganizationCreateResponseDto | None:
        """See :meth:`Organizations.create`."""
        return await self._client._invoke(
            _create_op.asyncio,
            body=_build_create_dto(name=name, slug=slug, description=description),
        )

    async def update(
        self,
        org_id: str,
        *,
        name: str,
        slug: str,
        description: str | None = None,
    ) -> OkResponseDto | None:
        """See :meth:`Organizations.update`."""
        return await self._client._invoke(
            _edit_op.asyncio,
            id=org_id,
            body=_build_create_dto(name=name, slug=slug, description=description),
        )

    async def delete(self, org_id: str) -> OkResponseDto | None:
        """See :meth:`Organizations.delete`."""
        return await self._client._invoke(_delete_op.asyncio, id=org_id)

    async def invite(
        self,
        org_id: str,
        email: str,
        *,
        role: CreateInvitationDtoDesiredRole | str = CreateInvitationDtoDesiredRole.USER,
    ) -> InvitationResponseDto | None:
        """See :meth:`Organizations.invite`."""
        return await self._client._invoke(
            _invite_op.asyncio,
            id=org_id,
            body=_build_invite_dto(email=email, role=role),
        )

    async def cancel_invitation(self, org_id: str, invitation_id: str) -> SuccessResponseDto | None:
        """See :meth:`Organizations.cancel_invitation`."""
        return await self._client._invoke(
            _delete_invite_op.asyncio, id=org_id, invitation_id=invitation_id
        )

    async def remove_member(self, org_id: str, user_id: str) -> SuccessResponseDto | None:
        """See :meth:`Organizations.remove_member`."""
        return await self._client._invoke(_remove_member_op.asyncio, id=org_id, user_id=user_id)

    async def transfer_ownership(
        self, org_id: str, target_user_id: str
    ) -> SuccessResponseDto | None:
        """See :meth:`Organizations.transfer_ownership`."""
        return await self._client._invoke(
            _transfer_op.asyncio,
            id=org_id,
            body=TransferOwnershipDto(user_id=target_user_id),
        )
