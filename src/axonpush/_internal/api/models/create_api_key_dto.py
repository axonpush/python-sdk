from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_api_key_dto_scopes_item import CreateApiKeyDtoScopesItem
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateApiKeyDto")


@_attrs_define
class CreateApiKeyDto:
    """
    Attributes:
        name (str):
        organization_id (str):
        app_id (str | Unset):
        environment_id (str | Unset): Environment this key is bound to. All events published with this key will be
            tagged with this environment (unless allowEnvironmentOverride=true and the request specifies a different one).
        allow_environment_override (bool | Unset): When true, the caller may override the env via X-Axonpush-Environment
            header or the event.environment field. Defaults to false for safety. Default: False.
        scopes (list[CreateApiKeyDtoScopesItem] | Unset):
    """

    name: str
    organization_id: str
    app_id: str | Unset = UNSET
    environment_id: str | Unset = UNSET
    allow_environment_override: bool | Unset = False
    scopes: list[CreateApiKeyDtoScopesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        organization_id = self.organization_id

        app_id = self.app_id

        environment_id = self.environment_id

        allow_environment_override = self.allow_environment_override

        scopes: list[str] | Unset = UNSET
        if not isinstance(self.scopes, Unset):
            scopes = []
            for scopes_item_data in self.scopes:
                scopes_item = scopes_item_data.value
                scopes.append(scopes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "organizationId": organization_id,
            }
        )
        if app_id is not UNSET:
            field_dict["appId"] = app_id
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id
        if allow_environment_override is not UNSET:
            field_dict["allowEnvironmentOverride"] = allow_environment_override
        if scopes is not UNSET:
            field_dict["scopes"] = scopes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        organization_id = d.pop("organizationId")

        app_id = d.pop("appId", UNSET)

        environment_id = d.pop("environmentId", UNSET)

        allow_environment_override = d.pop("allowEnvironmentOverride", UNSET)

        _scopes = d.pop("scopes", UNSET)
        scopes: list[CreateApiKeyDtoScopesItem] | Unset = UNSET
        if _scopes is not UNSET:
            scopes = []
            for scopes_item_data in _scopes:
                scopes_item = CreateApiKeyDtoScopesItem(scopes_item_data)

                scopes.append(scopes_item)

        create_api_key_dto = cls(
            name=name,
            organization_id=organization_id,
            app_id=app_id,
            environment_id=environment_id,
            allow_environment_override=allow_environment_override,
            scopes=scopes,
        )

        create_api_key_dto.additional_properties = d
        return create_api_key_dto

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
