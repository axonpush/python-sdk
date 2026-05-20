from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PlanVariantsDto")


@_attrs_define
class PlanVariantsDto:
    """
    Attributes:
        monthly (str | Unset):
        annual (str | Unset):
    """

    monthly: str | Unset = UNSET
    annual: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        monthly = self.monthly

        annual = self.annual

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if monthly is not UNSET:
            field_dict["monthly"] = monthly
        if annual is not UNSET:
            field_dict["annual"] = annual

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        monthly = d.pop("monthly", UNSET)

        annual = d.pop("annual", UNSET)

        plan_variants_dto = cls(
            monthly=monthly,
            annual=annual,
        )

        plan_variants_dto.additional_properties = d
        return plan_variants_dto

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
