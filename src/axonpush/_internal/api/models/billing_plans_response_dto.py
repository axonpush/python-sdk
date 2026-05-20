from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.plan_limits_dto import PlanLimitsDto


T = TypeVar("T", bound="BillingPlansResponseDto")


@_attrs_define
class BillingPlansResponseDto:
    """
    Attributes:
        plans (PlanLimitsDto):
    """

    plans: PlanLimitsDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.plan_limits_dto import PlanLimitsDto

        plans = self.plans.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plans": plans,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.plan_limits_dto import PlanLimitsDto

        d = dict(src_dict)
        plans = PlanLimitsDto.from_dict(d.pop("plans"))

        billing_plans_response_dto = cls(
            plans=plans,
        )

        billing_plans_response_dto.additional_properties = d
        return billing_plans_response_dto

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
