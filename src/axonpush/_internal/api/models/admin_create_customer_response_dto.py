from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
    from ..models.admin_org_list_item_dto import AdminOrgListItemDto


T = TypeVar("T", bound="AdminCreateCustomerResponseDto")


@_attrs_define
class AdminCreateCustomerResponseDto:
    """
    Attributes:
        org (AdminOrgListItemDto):
        invitation (AdminOrgInvitationDto):
    """

    org: AdminOrgListItemDto
    invitation: AdminOrgInvitationDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto

        org = self.org.to_dict()

        invitation = self.invitation.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "org": org,
                "invitation": invitation,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_org_invitation_dto import AdminOrgInvitationDto
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto

        d = dict(src_dict)
        org = AdminOrgListItemDto.from_dict(d.pop("org"))

        invitation = AdminOrgInvitationDto.from_dict(d.pop("invitation"))

        admin_create_customer_response_dto = cls(
            org=org,
            invitation=invitation,
        )

        admin_create_customer_response_dto.additional_properties = d
        return admin_create_customer_response_dto

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
