from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PublicIngestTokenResponseDto")


@_attrs_define
class PublicIngestTokenResponseDto:
    """
    Attributes:
        id (str):
        token_id (str):
        org_id (str):
        name (str):
        created_at (str):
        app_id (str | Unset):
        channel_id (str | Unset):
        environment_id (str | Unset):
        scopes (list[str] | Unset):
        prefix (str | Unset):
        last_used_at (str | Unset):
        revoked_at (str | Unset):
    """

    id: str
    token_id: str
    org_id: str
    name: str
    created_at: str
    app_id: str | Unset = UNSET
    channel_id: str | Unset = UNSET
    environment_id: str | Unset = UNSET
    scopes: list[str] | Unset = UNSET
    prefix: str | Unset = UNSET
    last_used_at: str | Unset = UNSET
    revoked_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        token_id = self.token_id

        org_id = self.org_id

        name = self.name

        created_at = self.created_at

        app_id = self.app_id

        channel_id = self.channel_id

        environment_id = self.environment_id

        scopes: list[str] | Unset = UNSET
        if not isinstance(self.scopes, Unset):
            scopes = self.scopes

        prefix = self.prefix

        last_used_at = self.last_used_at

        revoked_at = self.revoked_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tokenId": token_id,
                "orgId": org_id,
                "name": name,
                "createdAt": created_at,
            }
        )
        if app_id is not UNSET:
            field_dict["appId"] = app_id
        if channel_id is not UNSET:
            field_dict["channelId"] = channel_id
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if last_used_at is not UNSET:
            field_dict["lastUsedAt"] = last_used_at
        if revoked_at is not UNSET:
            field_dict["revokedAt"] = revoked_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        token_id = d.pop("tokenId")

        org_id = d.pop("orgId")

        name = d.pop("name")

        created_at = d.pop("createdAt")

        app_id = d.pop("appId", UNSET)

        channel_id = d.pop("channelId", UNSET)

        environment_id = d.pop("environmentId", UNSET)

        scopes = cast(list[str], d.pop("scopes", UNSET))

        prefix = d.pop("prefix", UNSET)

        last_used_at = d.pop("lastUsedAt", UNSET)

        revoked_at = d.pop("revokedAt", UNSET)

        public_ingest_token_response_dto = cls(
            id=id,
            token_id=token_id,
            org_id=org_id,
            name=name,
            created_at=created_at,
            app_id=app_id,
            channel_id=channel_id,
            environment_id=environment_id,
            scopes=scopes,
            prefix=prefix,
            last_used_at=last_used_at,
            revoked_at=revoked_at,
        )

        public_ingest_token_response_dto.additional_properties = d
        return public_ingest_token_response_dto

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
