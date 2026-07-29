from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.admin_set_status_dto_subscription_status import AdminSetStatusDtoSubscriptionStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminSetStatusDto")


@_attrs_define
class AdminSetStatusDto:
    """
    Attributes:
        subscription_status (AdminSetStatusDtoSubscriptionStatus):
    """

    subscription_status: AdminSetStatusDtoSubscriptionStatus
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subscription_status = self.subscription_status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subscriptionStatus": subscription_status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subscription_status = AdminSetStatusDtoSubscriptionStatus(d.pop("subscriptionStatus"))

        admin_set_status_dto = cls(
            subscription_status=subscription_status,
        )

        admin_set_status_dto.additional_properties = d
        return admin_set_status_dto

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
