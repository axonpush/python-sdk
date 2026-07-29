from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_user_list_item_dto import AdminUserListItemDto


T = TypeVar("T", bound="AdminUserListDto")


@_attrs_define
class AdminUserListDto:
    """
    Attributes:
        total (float):
        truncated (bool):
        users (list[AdminUserListItemDto]):
    """

    total: float
    truncated: bool
    users: list[AdminUserListItemDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_user_list_item_dto import AdminUserListItemDto

        total = self.total

        truncated = self.truncated

        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()
            users.append(users_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "truncated": truncated,
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_user_list_item_dto import AdminUserListItemDto

        d = dict(src_dict)
        total = d.pop("total")

        truncated = d.pop("truncated")

        users = []
        _users = d.pop("users")
        for users_item_data in _users:
            users_item = AdminUserListItemDto.from_dict(users_item_data)

            users.append(users_item)

        admin_user_list_dto = cls(
            total=total,
            truncated=truncated,
            users=users,
        )

        admin_user_list_dto.additional_properties = d
        return admin_user_list_dto

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
