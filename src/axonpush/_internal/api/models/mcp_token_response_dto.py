from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mcp_token_response_dto_access import McpTokenResponseDtoAccess
from ..types import UNSET, Unset

T = TypeVar("T", bound="McpTokenResponseDto")


@_attrs_define
class McpTokenResponseDto:
    """
    Attributes:
        id (str):
        name (str):
        prefix (str):
        access (McpTokenResponseDtoAccess):
        scopes (list[str]):
        created_at (str):
        expires_at (str):
        last_used_at (str | Unset):
    """

    id: str
    name: str
    prefix: str
    access: McpTokenResponseDtoAccess
    scopes: list[str]
    created_at: str
    expires_at: str
    last_used_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        prefix = self.prefix

        access = self.access.value

        scopes = self.scopes

        created_at = self.created_at

        expires_at = self.expires_at

        last_used_at = self.last_used_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "prefix": prefix,
                "access": access,
                "scopes": scopes,
                "createdAt": created_at,
                "expiresAt": expires_at,
            }
        )
        if last_used_at is not UNSET:
            field_dict["lastUsedAt"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        prefix = d.pop("prefix")

        access = McpTokenResponseDtoAccess(d.pop("access"))

        scopes = cast(list[str], d.pop("scopes"))

        created_at = d.pop("createdAt")

        expires_at = d.pop("expiresAt")

        last_used_at = d.pop("lastUsedAt", UNSET)

        mcp_token_response_dto = cls(
            id=id,
            name=name,
            prefix=prefix,
            access=access,
            scopes=scopes,
            created_at=created_at,
            expires_at=expires_at,
            last_used_at=last_used_at,
        )

        mcp_token_response_dto.additional_properties = d
        return mcp_token_response_dto

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
