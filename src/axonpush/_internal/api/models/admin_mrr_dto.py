from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.mrr_by_plan_dto import MrrByPlanDto


T = TypeVar("T", bound="AdminMrrDto")


@_attrs_define
class AdminMrrDto:
    """
    Attributes:
        estimate_usd (float): Approximate monthly recurring revenue (USD)
        paying_orgs (float):
        by_plan (list[MrrByPlanDto]):
    """

    estimate_usd: float
    paying_orgs: float
    by_plan: list[MrrByPlanDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.mrr_by_plan_dto import MrrByPlanDto

        estimate_usd = self.estimate_usd

        paying_orgs = self.paying_orgs

        by_plan = []
        for by_plan_item_data in self.by_plan:
            by_plan_item = by_plan_item_data.to_dict()
            by_plan.append(by_plan_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "estimateUsd": estimate_usd,
                "payingOrgs": paying_orgs,
                "byPlan": by_plan,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mrr_by_plan_dto import MrrByPlanDto

        d = dict(src_dict)
        estimate_usd = d.pop("estimateUsd")

        paying_orgs = d.pop("payingOrgs")

        by_plan = []
        _by_plan = d.pop("byPlan")
        for by_plan_item_data in _by_plan:
            by_plan_item = MrrByPlanDto.from_dict(by_plan_item_data)

            by_plan.append(by_plan_item)

        admin_mrr_dto = cls(
            estimate_usd=estimate_usd,
            paying_orgs=paying_orgs,
            by_plan=by_plan,
        )

        admin_mrr_dto.additional_properties = d
        return admin_mrr_dto

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
