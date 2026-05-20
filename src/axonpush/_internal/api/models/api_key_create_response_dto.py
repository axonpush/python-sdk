from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_create_response_dto_scopes_item import ApiKeyCreateResponseDtoScopesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyCreateResponseDto")


@_attrs_define
class ApiKeyCreateResponseDto:
    """
    Attributes:
        id (str):
        name (str):
        key (str): Raw API key, only returned at creation time
        scopes (list[ApiKeyCreateResponseDtoScopesItem]):
        allow_environment_override (bool):
        created_at (str):
        prefix (str | Unset):
        environment_id (str | Unset):
    """

    id: str
    name: str
    key: str
    scopes: list[ApiKeyCreateResponseDtoScopesItem]
    allow_environment_override: bool
    created_at: str
    prefix: str | Unset = UNSET
    environment_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        key = self.key

        scopes = []
        for scopes_item_data in self.scopes:
            scopes_item = scopes_item_data.value
            scopes.append(scopes_item)

        allow_environment_override = self.allow_environment_override

        created_at = self.created_at

        prefix = self.prefix

        environment_id = self.environment_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "key": key,
                "scopes": scopes,
                "allowEnvironmentOverride": allow_environment_override,
                "createdAt": created_at,
            }
        )
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        key = d.pop("key")

        scopes = []
        _scopes = d.pop("scopes")
        for scopes_item_data in _scopes:
            scopes_item = ApiKeyCreateResponseDtoScopesItem(scopes_item_data)

            scopes.append(scopes_item)

        allow_environment_override = d.pop("allowEnvironmentOverride")

        created_at = d.pop("createdAt")

        prefix = d.pop("prefix", UNSET)

        environment_id = d.pop("environmentId", UNSET)

        api_key_create_response_dto = cls(
            id=id,
            name=name,
            key=key,
            scopes=scopes,
            allow_environment_override=allow_environment_override,
            created_at=created_at,
            prefix=prefix,
            environment_id=environment_id,
        )

        api_key_create_response_dto.additional_properties = d
        return api_key_create_response_dto

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
