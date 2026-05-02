from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateEnvironmentDto")


@_attrs_define
class CreateEnvironmentDto:
    """
    Attributes:
        name (str):
        slug (str | Unset):
        color (str | Unset):
        is_production (bool | Unset):
        is_default (bool | Unset):
        clone_from_env_id (str | Unset):
    """

    name: str
    slug: str | Unset = UNSET
    color: str | Unset = UNSET
    is_production: bool | Unset = UNSET
    is_default: bool | Unset = UNSET
    clone_from_env_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        slug = self.slug

        color = self.color

        is_production = self.is_production

        is_default = self.is_default

        clone_from_env_id = self.clone_from_env_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if slug is not UNSET:
            field_dict["slug"] = slug
        if color is not UNSET:
            field_dict["color"] = color
        if is_production is not UNSET:
            field_dict["isProduction"] = is_production
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default
        if clone_from_env_id is not UNSET:
            field_dict["cloneFromEnvId"] = clone_from_env_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        slug = d.pop("slug", UNSET)

        color = d.pop("color", UNSET)

        is_production = d.pop("isProduction", UNSET)

        is_default = d.pop("isDefault", UNSET)

        clone_from_env_id = d.pop("cloneFromEnvId", UNSET)

        create_environment_dto = cls(
            name=name,
            slug=slug,
            color=color,
            is_production=is_production,
            is_default=is_default,
            clone_from_env_id=clone_from_env_id,
        )

        create_environment_dto.additional_properties = d
        return create_environment_dto

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
