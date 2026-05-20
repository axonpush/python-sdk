from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateReleaseDto")


@_attrs_define
class CreateReleaseDto:
    """
    Attributes:
        version (str):
        projects (list[str] | Unset):
        date_released (str | Unset):
    """

    version: str
    projects: list[str] | Unset = UNSET
    date_released: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version = self.version

        projects: list[str] | Unset = UNSET
        if not isinstance(self.projects, Unset):
            projects = self.projects

        date_released = self.date_released

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "version": version,
            }
        )
        if projects is not UNSET:
            field_dict["projects"] = projects
        if date_released is not UNSET:
            field_dict["dateReleased"] = date_released

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        version = d.pop("version")

        projects = cast(list[str], d.pop("projects", UNSET))

        date_released = d.pop("dateReleased", UNSET)

        create_release_dto = cls(
            version=version,
            projects=projects,
            date_released=date_released,
        )

        create_release_dto.additional_properties = d
        return create_release_dto

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
