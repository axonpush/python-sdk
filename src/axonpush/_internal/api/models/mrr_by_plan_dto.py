from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MrrByPlanDto")


@_attrs_define
class MrrByPlanDto:
    """
    Attributes:
        plan (str):
        count (float):
        mrr_usd (float): Estimated monthly recurring revenue (USD) from this plan
    """

    plan: str
    count: float
    mrr_usd: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan = self.plan

        count = self.count

        mrr_usd = self.mrr_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plan": plan,
                "count": count,
                "mrrUsd": mrr_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        plan = d.pop("plan")

        count = d.pop("count")

        mrr_usd = d.pop("mrrUsd")

        mrr_by_plan_dto = cls(
            plan=plan,
            count=count,
            mrr_usd=mrr_usd,
        )

        mrr_by_plan_dto.additional_properties = d
        return mrr_by_plan_dto

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
