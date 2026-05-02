from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_response_dto import UserResponseDto


T = TypeVar("T", bound="SwitchActiveOrgResponseDto")


@_attrs_define
class SwitchActiveOrgResponseDto:
    """
    Attributes:
        access_token (str):
        refresh_token (str):
        user (UserResponseDto | Unset):
    """

    access_token: str
    refresh_token: str
    user: UserResponseDto | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.user_response_dto import UserResponseDto

        access_token = self.access_token

        refresh_token = self.refresh_token

        user: dict[str, Any] | Unset = UNSET
        if not isinstance(self.user, Unset):
            user = self.user.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )
        if user is not UNSET:
            field_dict["user"] = user

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_response_dto import UserResponseDto

        d = dict(src_dict)
        access_token = d.pop("access_token")

        refresh_token = d.pop("refresh_token")

        _user = d.pop("user", UNSET)
        user: UserResponseDto | Unset
        if isinstance(_user, Unset):
            user = UNSET
        else:
            user = UserResponseDto.from_dict(_user)

        switch_active_org_response_dto = cls(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user,
        )

        switch_active_org_response_dto.additional_properties = d
        return switch_active_org_response_dto

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
