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
        api_key_id (str):
        org_id (str):
        name (str):
        scopes (list[ApiKeyCreateResponseDtoScopesItem]):
        allow_environment_override (bool):
        created_at (str):
        key (str): Raw API key, only returned at creation time
        app_id (str | Unset):
        environment_id (str | Unset):
        prefix (str | Unset):
        last_used_at (str | Unset):
        updated_at (str | Unset):
        revoked_at (str | Unset):
    """

    id: str
    api_key_id: str
    org_id: str
    name: str
    scopes: list[ApiKeyCreateResponseDtoScopesItem]
    allow_environment_override: bool
    created_at: str
    key: str
    app_id: str | Unset = UNSET
    environment_id: str | Unset = UNSET
    prefix: str | Unset = UNSET
    last_used_at: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    revoked_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        api_key_id = self.api_key_id

        org_id = self.org_id

        name = self.name

        scopes = []
        for scopes_item_data in self.scopes:
            scopes_item = scopes_item_data.value
            scopes.append(scopes_item)

        allow_environment_override = self.allow_environment_override

        created_at = self.created_at

        key = self.key

        app_id = self.app_id

        environment_id = self.environment_id

        prefix = self.prefix

        last_used_at = self.last_used_at

        updated_at = self.updated_at

        revoked_at = self.revoked_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "apiKeyId": api_key_id,
                "orgId": org_id,
                "name": name,
                "scopes": scopes,
                "allowEnvironmentOverride": allow_environment_override,
                "createdAt": created_at,
                "key": key,
            }
        )
        if app_id is not UNSET:
            field_dict["appId"] = app_id
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if last_used_at is not UNSET:
            field_dict["lastUsedAt"] = last_used_at
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if revoked_at is not UNSET:
            field_dict["revokedAt"] = revoked_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        api_key_id = d.pop("apiKeyId")

        org_id = d.pop("orgId")

        name = d.pop("name")

        scopes = []
        _scopes = d.pop("scopes")
        for scopes_item_data in _scopes:
            scopes_item = ApiKeyCreateResponseDtoScopesItem(scopes_item_data)

            scopes.append(scopes_item)

        allow_environment_override = d.pop("allowEnvironmentOverride")

        created_at = d.pop("createdAt")

        key = d.pop("key")

        app_id = d.pop("appId", UNSET)

        environment_id = d.pop("environmentId", UNSET)

        prefix = d.pop("prefix", UNSET)

        last_used_at = d.pop("lastUsedAt", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        revoked_at = d.pop("revokedAt", UNSET)

        api_key_create_response_dto = cls(
            id=id,
            api_key_id=api_key_id,
            org_id=org_id,
            name=name,
            scopes=scopes,
            allow_environment_override=allow_environment_override,
            created_at=created_at,
            key=key,
            app_id=app_id,
            environment_id=environment_id,
            prefix=prefix,
            last_used_at=last_used_at,
            updated_at=updated_at,
            revoked_at=revoked_at,
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
