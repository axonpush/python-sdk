from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminUpdateBillingDto")


@_attrs_define
class AdminUpdateBillingDto:
    """
    Attributes:
        billing_monthly_amount_usd (float):
        billing_notes (str | Unset):
    """

    billing_monthly_amount_usd: float
    billing_notes: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        billing_monthly_amount_usd = self.billing_monthly_amount_usd

        billing_notes = self.billing_notes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "billingMonthlyAmountUsd": billing_monthly_amount_usd,
            }
        )
        if billing_notes is not UNSET:
            field_dict["billingNotes"] = billing_notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        billing_monthly_amount_usd = d.pop("billingMonthlyAmountUsd")

        billing_notes = d.pop("billingNotes", UNSET)

        admin_update_billing_dto = cls(
            billing_monthly_amount_usd=billing_monthly_amount_usd,
            billing_notes=billing_notes,
        )

        admin_update_billing_dto.additional_properties = d
        return admin_update_billing_dto

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
