from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="InvitationResponseDto")


@_attrs_define
class InvitationResponseDto:
    """
    Attributes:
        id (str):
        invitation_id (str):
        org_id (str):
        invited_email (str):
        role (str):
        status (str):
        created_at (str):
        invite_role (str | Unset):
        code (str | Unset):
        expires_at (str | Unset):
        accepted_at (str | Unset):
        updated_at (str | Unset):
    """

    id: str
    invitation_id: str
    org_id: str
    invited_email: str
    role: str
    status: str
    created_at: str
    invite_role: str | Unset = UNSET
    code: str | Unset = UNSET
    expires_at: str | Unset = UNSET
    accepted_at: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        invitation_id = self.invitation_id

        org_id = self.org_id

        invited_email = self.invited_email

        role = self.role

        status = self.status

        created_at = self.created_at

        invite_role = self.invite_role

        code = self.code

        expires_at = self.expires_at

        accepted_at = self.accepted_at

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "invitationId": invitation_id,
                "orgId": org_id,
                "invitedEmail": invited_email,
                "role": role,
                "status": status,
                "createdAt": created_at,
            }
        )
        if invite_role is not UNSET:
            field_dict["inviteRole"] = invite_role
        if code is not UNSET:
            field_dict["code"] = code
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
        if accepted_at is not UNSET:
            field_dict["acceptedAt"] = accepted_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        invitation_id = d.pop("invitationId")

        org_id = d.pop("orgId")

        invited_email = d.pop("invitedEmail")

        role = d.pop("role")

        status = d.pop("status")

        created_at = d.pop("createdAt")

        invite_role = d.pop("inviteRole", UNSET)

        code = d.pop("code", UNSET)

        expires_at = d.pop("expiresAt", UNSET)

        accepted_at = d.pop("acceptedAt", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        invitation_response_dto = cls(
            id=id,
            invitation_id=invitation_id,
            org_id=org_id,
            invited_email=invited_email,
            role=role,
            status=status,
            created_at=created_at,
            invite_role=invite_role,
            code=code,
            expires_at=expires_at,
            accepted_at=accepted_at,
            updated_at=updated_at,
        )

        invitation_response_dto.additional_properties = d
        return invitation_response_dto

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
