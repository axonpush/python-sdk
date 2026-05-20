from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.plan_features_dto import PlanFeaturesDto
    from ..models.plan_variants_dto import PlanVariantsDto


T = TypeVar("T", bound="PlanLimitsDto")


@_attrs_define
class PlanLimitsDto:
    """
    Attributes:
        events (float | None):
        retention_days (float | None):
        seats (float | None):
        features (PlanFeaturesDto):
        lemonsqueezy_variants (PlanVariantsDto | Unset):
    """

    events: float | None
    retention_days: float | None
    seats: float | None
    features: PlanFeaturesDto
    lemonsqueezy_variants: PlanVariantsDto | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.plan_features_dto import PlanFeaturesDto
        from ..models.plan_variants_dto import PlanVariantsDto

        events: float | None
        events = self.events

        retention_days: float | None
        retention_days = self.retention_days

        seats: float | None
        seats = self.seats

        features = self.features.to_dict()

        lemonsqueezy_variants: dict[str, Any] | Unset = UNSET
        if not isinstance(self.lemonsqueezy_variants, Unset):
            lemonsqueezy_variants = self.lemonsqueezy_variants.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "events": events,
                "retentionDays": retention_days,
                "seats": seats,
                "features": features,
            }
        )
        if lemonsqueezy_variants is not UNSET:
            field_dict["lemonsqueezyVariants"] = lemonsqueezy_variants

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.plan_features_dto import PlanFeaturesDto
        from ..models.plan_variants_dto import PlanVariantsDto

        d = dict(src_dict)

        def _parse_events(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        events = _parse_events(d.pop("events"))

        def _parse_retention_days(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        retention_days = _parse_retention_days(d.pop("retentionDays"))

        def _parse_seats(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        seats = _parse_seats(d.pop("seats"))

        features = PlanFeaturesDto.from_dict(d.pop("features"))

        _lemonsqueezy_variants = d.pop("lemonsqueezyVariants", UNSET)
        lemonsqueezy_variants: PlanVariantsDto | Unset
        if isinstance(_lemonsqueezy_variants, Unset):
            lemonsqueezy_variants = UNSET
        else:
            lemonsqueezy_variants = PlanVariantsDto.from_dict(_lemonsqueezy_variants)

        plan_limits_dto = cls(
            events=events,
            retention_days=retention_days,
            seats=seats,
            features=features,
            lemonsqueezy_variants=lemonsqueezy_variants,
        )

        plan_limits_dto.additional_properties = d
        return plan_limits_dto

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
