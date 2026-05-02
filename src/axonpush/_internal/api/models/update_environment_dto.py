from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateEnvironmentDto")


@_attrs_define
class UpdateEnvironmentDto:
    """
    Attributes:
        name (str | Unset):
        color (str | Unset):
        require_confirmation_for_destructive (bool | Unset):
    """

    name: str | Unset = UNSET
    color: str | Unset = UNSET
    require_confirmation_for_destructive: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        color = self.color

        require_confirmation_for_destructive = self.require_confirmation_for_destructive

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if color is not UNSET:
            field_dict["color"] = color
        if require_confirmation_for_destructive is not UNSET:
            field_dict["requireConfirmationForDestructive"] = require_confirmation_for_destructive

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        color = d.pop("color", UNSET)

        require_confirmation_for_destructive = d.pop("requireConfirmationForDestructive", UNSET)

        update_environment_dto = cls(
            name=name,
            color=color,
            require_confirmation_for_destructive=require_confirmation_for_destructive,
        )

        update_environment_dto.additional_properties = d
        return update_environment_dto

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
