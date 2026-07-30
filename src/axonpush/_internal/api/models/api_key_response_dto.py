from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.api_key_response_dto_purpose import ApiKeyResponseDtoPurpose
from ..models.api_key_response_dto_scopes_item import ApiKeyResponseDtoScopesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="ApiKeyResponseDto")


@_attrs_define
class ApiKeyResponseDto:
    """
    Attributes:
        id (str):
        name (str):
        scopes (list[ApiKeyResponseDtoScopesItem]):
        allow_environment_override (bool):
        created_at (str):
        app_id (str | Unset):
        environment_id (str | Unset):
        purpose (ApiKeyResponseDtoPurpose | Unset):
        prefix (str | Unset):
        last_used_at (str | Unset):
    """

    id: str
    name: str
    scopes: list[ApiKeyResponseDtoScopesItem]
    allow_environment_override: bool
    created_at: str
    app_id: str | Unset = UNSET
    environment_id: str | Unset = UNSET
    purpose: ApiKeyResponseDtoPurpose | Unset = UNSET
    prefix: str | Unset = UNSET
    last_used_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        scopes = []
        for scopes_item_data in self.scopes:
            scopes_item = scopes_item_data.value
            scopes.append(scopes_item)

        allow_environment_override = self.allow_environment_override

        created_at = self.created_at

        app_id = self.app_id

        environment_id = self.environment_id

        purpose: str | Unset = UNSET
        if not isinstance(self.purpose, Unset):
            purpose = self.purpose.value

        prefix = self.prefix

        last_used_at = self.last_used_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "scopes": scopes,
                "allowEnvironmentOverride": allow_environment_override,
                "createdAt": created_at,
            }
        )
        if app_id is not UNSET:
            field_dict["appId"] = app_id
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id
        if purpose is not UNSET:
            field_dict["purpose"] = purpose
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if last_used_at is not UNSET:
            field_dict["lastUsedAt"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        scopes = []
        _scopes = d.pop("scopes")
        for scopes_item_data in _scopes:
            scopes_item = ApiKeyResponseDtoScopesItem(scopes_item_data)

            scopes.append(scopes_item)

        allow_environment_override = d.pop("allowEnvironmentOverride")

        created_at = d.pop("createdAt")

        app_id = d.pop("appId", UNSET)

        environment_id = d.pop("environmentId", UNSET)

        _purpose = d.pop("purpose", UNSET)
        purpose: ApiKeyResponseDtoPurpose | Unset
        if isinstance(_purpose, Unset):
            purpose = UNSET
        else:
            purpose = ApiKeyResponseDtoPurpose(_purpose)

        prefix = d.pop("prefix", UNSET)

        last_used_at = d.pop("lastUsedAt", UNSET)

        api_key_response_dto = cls(
            id=id,
            name=name,
            scopes=scopes,
            allow_environment_override=allow_environment_override,
            created_at=created_at,
            app_id=app_id,
            environment_id=environment_id,
            purpose=purpose,
            prefix=prefix,
            last_used_at=last_used_at,
        )

        api_key_response_dto.additional_properties = d
        return api_key_response_dto

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
