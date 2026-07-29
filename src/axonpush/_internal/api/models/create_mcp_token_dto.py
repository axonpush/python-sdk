from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_mcp_token_dto_access import CreateMcpTokenDtoAccess
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateMcpTokenDto")


@_attrs_define
class CreateMcpTokenDto:
    """
    Attributes:
        name (str):  Example: My coding agent.
        access (CreateMcpTokenDtoAccess):
    """

    name: str
    access: CreateMcpTokenDtoAccess
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        access = self.access.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "access": access,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        access = CreateMcpTokenDtoAccess(d.pop("access"))

        create_mcp_token_dto = cls(
            name=name,
            access=access,
        )

        create_mcp_token_dto.additional_properties = d
        return create_mcp_token_dto

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
