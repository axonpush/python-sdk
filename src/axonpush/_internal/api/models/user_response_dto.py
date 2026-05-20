from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_response_dto_roles_item import UserResponseDtoRolesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserResponseDto")


@_attrs_define
class UserResponseDto:
    """
    Attributes:
        id (str):
        first_name (str):
        last_name (str):
        email (str):
        username (str):
        google_id (None | str):
        roles (list[UserResponseDtoRolesItem]):
        organization_id (None | str):
        deleted_at (None | str | Unset):
    """

    id: str
    first_name: str
    last_name: str
    email: str
    username: str
    google_id: None | str
    roles: list[UserResponseDtoRolesItem]
    organization_id: None | str
    deleted_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        first_name = self.first_name

        last_name = self.last_name

        email = self.email

        username = self.username

        google_id: None | str
        google_id = self.google_id

        roles = []
        for roles_item_data in self.roles:
            roles_item = roles_item_data.value
            roles.append(roles_item)

        organization_id: None | str
        organization_id = self.organization_id

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "username": username,
                "googleId": google_id,
                "roles": roles,
                "organizationId": organization_id,
            }
        )
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        first_name = d.pop("first_name")

        last_name = d.pop("last_name")

        email = d.pop("email")

        username = d.pop("username")

        def _parse_google_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        google_id = _parse_google_id(d.pop("googleId"))

        roles = []
        _roles = d.pop("roles")
        for roles_item_data in _roles:
            roles_item = UserResponseDtoRolesItem(roles_item_data)

            roles.append(roles_item)

        def _parse_organization_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        organization_id = _parse_organization_id(d.pop("organizationId"))

        def _parse_deleted_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deletedAt", UNSET))

        user_response_dto = cls(
            id=id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            google_id=google_id,
            roles=roles,
            organization_id=organization_id,
            deleted_at=deleted_at,
        )

        user_response_dto.additional_properties = d
        return user_response_dto

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
