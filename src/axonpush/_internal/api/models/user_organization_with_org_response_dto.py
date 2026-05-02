from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.organization_response_dto import OrganizationResponseDto


T = TypeVar("T", bound="UserOrganizationWithOrgResponseDto")


@_attrs_define
class UserOrganizationWithOrgResponseDto:
    """
    Attributes:
        user_id (str):
        org_id (str):
        role (str):
        joined_at (str):
        deleted_at (str | Unset):
        organization (None | OrganizationResponseDto | Unset):
    """

    user_id: str
    org_id: str
    role: str
    joined_at: str
    deleted_at: str | Unset = UNSET
    organization: None | OrganizationResponseDto | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.organization_response_dto import OrganizationResponseDto

        user_id = self.user_id

        org_id = self.org_id

        role = self.role

        joined_at = self.joined_at

        deleted_at = self.deleted_at

        organization: dict[str, Any] | None | Unset
        if isinstance(self.organization, Unset):
            organization = UNSET
        elif isinstance(self.organization, OrganizationResponseDto):
            organization = self.organization.to_dict()
        else:
            organization = self.organization

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "userId": user_id,
                "orgId": org_id,
                "role": role,
                "joinedAt": joined_at,
            }
        )
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if organization is not UNSET:
            field_dict["organization"] = organization

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization_response_dto import OrganizationResponseDto

        d = dict(src_dict)
        user_id = d.pop("userId")

        org_id = d.pop("orgId")

        role = d.pop("role")

        joined_at = d.pop("joinedAt")

        deleted_at = d.pop("deletedAt", UNSET)

        def _parse_organization(data: object) -> None | OrganizationResponseDto | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                organization_type_1 = OrganizationResponseDto.from_dict(data)

                return organization_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrganizationResponseDto | Unset, data)

        organization = _parse_organization(d.pop("organization", UNSET))

        user_organization_with_org_response_dto = cls(
            user_id=user_id,
            org_id=org_id,
            role=role,
            joined_at=joined_at,
            deleted_at=deleted_at,
            organization=organization,
        )

        user_organization_with_org_response_dto.additional_properties = d
        return user_organization_with_org_response_dto

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
