from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.billing_checkout_request_dto_cadence import BillingCheckoutRequestDtoCadence
from ..models.billing_checkout_request_dto_plan import BillingCheckoutRequestDtoPlan
from ..types import UNSET, Unset

T = TypeVar("T", bound="BillingCheckoutRequestDto")


@_attrs_define
class BillingCheckoutRequestDto:
    """
    Attributes:
        plan (BillingCheckoutRequestDtoPlan):
        cadence (BillingCheckoutRequestDtoCadence | Unset):  Default: BillingCheckoutRequestDtoCadence.MONTHLY.
    """

    plan: BillingCheckoutRequestDtoPlan
    cadence: BillingCheckoutRequestDtoCadence | Unset = BillingCheckoutRequestDtoCadence.MONTHLY
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan = self.plan.value

        cadence: str | Unset = UNSET
        if not isinstance(self.cadence, Unset):
            cadence = self.cadence.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plan": plan,
            }
        )
        if cadence is not UNSET:
            field_dict["cadence"] = cadence

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        plan = BillingCheckoutRequestDtoPlan(d.pop("plan"))

        _cadence = d.pop("cadence", UNSET)
        cadence: BillingCheckoutRequestDtoCadence | Unset
        if isinstance(_cadence, Unset):
            cadence = UNSET
        else:
            cadence = BillingCheckoutRequestDtoCadence(_cadence)

        billing_checkout_request_dto = cls(
            plan=plan,
            cadence=cadence,
        )

        billing_checkout_request_dto.additional_properties = d
        return billing_checkout_request_dto

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
