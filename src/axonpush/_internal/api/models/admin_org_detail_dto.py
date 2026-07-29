from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
    from ..models.admin_org_limits_dto import AdminOrgLimitsDto
    from ..models.admin_org_list_item_dto import AdminOrgListItemDto
    from ..models.admin_org_member_dto import AdminOrgMemberDto


T = TypeVar("T", bound="AdminOrgDetailDto")


@_attrs_define
class AdminOrgDetailDto:
    """
    Attributes:
        org (AdminOrgListItemDto):
        limits (AdminOrgLimitsDto):
        members (list[AdminOrgMemberDto]):
        invitations (list[AdminOrgInvitationDto]):
    """

    org: AdminOrgListItemDto
    limits: AdminOrgLimitsDto
    members: list[AdminOrgMemberDto]
    invitations: list[AdminOrgInvitationDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
        from ..models.admin_org_limits_dto import AdminOrgLimitsDto
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto
        from ..models.admin_org_member_dto import AdminOrgMemberDto

        org = self.org.to_dict()

        limits = self.limits.to_dict()

        members = []
        for members_item_data in self.members:
            members_item = members_item_data.to_dict()
            members.append(members_item)

        invitations = []
        for invitations_item_data in self.invitations:
            invitations_item = invitations_item_data.to_dict()
            invitations.append(invitations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org": org,
                "limits": limits,
                "members": members,
                "invitations": invitations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
        from ..models.admin_org_limits_dto import AdminOrgLimitsDto
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto
        from ..models.admin_org_member_dto import AdminOrgMemberDto

        d = dict(src_dict)
        org = AdminOrgListItemDto.from_dict(d.pop("org"))

        limits = AdminOrgLimitsDto.from_dict(d.pop("limits"))

        members = []
        _members = d.pop("members")
        for members_item_data in _members:
            members_item = AdminOrgMemberDto.from_dict(members_item_data)

            members.append(members_item)

        invitations = []
        _invitations = d.pop("invitations")
        for invitations_item_data in _invitations:
            invitations_item = AdminOrgInvitationDto.from_dict(invitations_item_data)

            invitations.append(invitations_item)

        admin_org_detail_dto = cls(
            org=org,
            limits=limits,
            members=members,
            invitations=invitations,
        )

        admin_org_detail_dto.additional_properties = d
        return admin_org_detail_dto

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
