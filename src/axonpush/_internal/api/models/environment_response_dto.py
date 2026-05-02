from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EnvironmentResponseDto")


@_attrs_define
class EnvironmentResponseDto:
    """
    Attributes:
        id (str):
        environment_id (str):
        org_id (str):
        name (str):
        slug (str):
        created_at (str):
        color (str | Unset):
        is_default (bool | Unset):
        is_production (bool | Unset):
        is_ephemeral (bool | Unset):
        expires_at (str | Unset):
        updated_at (str | Unset):
        deleted_at (str | Unset):
    """

    id: str
    environment_id: str
    org_id: str
    name: str
    slug: str
    created_at: str
    color: str | Unset = UNSET
    is_default: bool | Unset = UNSET
    is_production: bool | Unset = UNSET
    is_ephemeral: bool | Unset = UNSET
    expires_at: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        environment_id = self.environment_id

        org_id = self.org_id

        name = self.name

        slug = self.slug

        created_at = self.created_at

        color = self.color

        is_default = self.is_default

        is_production = self.is_production

        is_ephemeral = self.is_ephemeral

        expires_at = self.expires_at

        updated_at = self.updated_at

        deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "environmentId": environment_id,
                "orgId": org_id,
                "name": name,
                "slug": slug,
                "createdAt": created_at,
            }
        )
        if color is not UNSET:
            field_dict["color"] = color
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default
        if is_production is not UNSET:
            field_dict["isProduction"] = is_production
        if is_ephemeral is not UNSET:
            field_dict["isEphemeral"] = is_ephemeral
        if expires_at is not UNSET:
            field_dict["expiresAt"] = expires_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        environment_id = d.pop("environmentId")

        org_id = d.pop("orgId")

        name = d.pop("name")

        slug = d.pop("slug")

        created_at = d.pop("createdAt")

        color = d.pop("color", UNSET)

        is_default = d.pop("isDefault", UNSET)

        is_production = d.pop("isProduction", UNSET)

        is_ephemeral = d.pop("isEphemeral", UNSET)

        expires_at = d.pop("expiresAt", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        environment_response_dto = cls(
            id=id,
            environment_id=environment_id,
            org_id=org_id,
            name=name,
            slug=slug,
            created_at=created_at,
            color=color,
            is_default=is_default,
            is_production=is_production,
            is_ephemeral=is_ephemeral,
            expires_at=expires_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        environment_response_dto.additional_properties = d
        return environment_response_dto

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
