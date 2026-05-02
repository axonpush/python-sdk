from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GoogleAuthResponseDto")


@_attrs_define
class GoogleAuthResponseDto:
    """
    Attributes:
        access_token (str):
        refresh_token (str):
        needs_org (bool | Unset):
    """

    access_token: str
    refresh_token: str
    needs_org: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        refresh_token = self.refresh_token

        needs_org = self.needs_org

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )
        if needs_org is not UNSET:
            field_dict["needsOrg"] = needs_org

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("access_token")

        refresh_token = d.pop("refresh_token")

        needs_org = d.pop("needsOrg", UNSET)

        google_auth_response_dto = cls(
            access_token=access_token,
            refresh_token=refresh_token,
            needs_org=needs_org,
        )

        google_auth_response_dto.additional_properties = d
        return google_auth_response_dto

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
