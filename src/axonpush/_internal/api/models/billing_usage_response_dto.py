from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.billing_usage_response_dto_subscription_status import (
    BillingUsageResponseDtoSubscriptionStatus,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="BillingUsageResponseDto")


@_attrs_define
class BillingUsageResponseDto:
    """
    Attributes:
        plan (str):
        used (float):
        subscription_status (BillingUsageResponseDtoSubscriptionStatus):
        limit (float | None | Unset):
        retention_days (float | None | Unset):
        seats (float | None | Unset):
        cycle_started_at (None | str | Unset):
        trial_ends_at (None | str | Unset): ISO timestamp; null when no trial active
    """

    plan: str
    used: float
    subscription_status: BillingUsageResponseDtoSubscriptionStatus
    limit: float | None | Unset = UNSET
    retention_days: float | None | Unset = UNSET
    seats: float | None | Unset = UNSET
    cycle_started_at: None | str | Unset = UNSET
    trial_ends_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan = self.plan

        used = self.used

        subscription_status = self.subscription_status.value

        limit: float | None | Unset
        if isinstance(self.limit, Unset):
            limit = UNSET
        else:
            limit = self.limit

        retention_days: float | None | Unset
        if isinstance(self.retention_days, Unset):
            retention_days = UNSET
        else:
            retention_days = self.retention_days

        seats: float | None | Unset
        if isinstance(self.seats, Unset):
            seats = UNSET
        else:
            seats = self.seats

        cycle_started_at: None | str | Unset
        if isinstance(self.cycle_started_at, Unset):
            cycle_started_at = UNSET
        else:
            cycle_started_at = self.cycle_started_at

        trial_ends_at: None | str | Unset
        if isinstance(self.trial_ends_at, Unset):
            trial_ends_at = UNSET
        else:
            trial_ends_at = self.trial_ends_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plan": plan,
                "used": used,
                "subscriptionStatus": subscription_status,
            }
        )
        if limit is not UNSET:
            field_dict["limit"] = limit
        if retention_days is not UNSET:
            field_dict["retentionDays"] = retention_days
        if seats is not UNSET:
            field_dict["seats"] = seats
        if cycle_started_at is not UNSET:
            field_dict["cycleStartedAt"] = cycle_started_at
        if trial_ends_at is not UNSET:
            field_dict["trialEndsAt"] = trial_ends_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        plan = d.pop("plan")

        used = d.pop("used")

        subscription_status = BillingUsageResponseDtoSubscriptionStatus(d.pop("subscriptionStatus"))

        def _parse_limit(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        limit = _parse_limit(d.pop("limit", UNSET))

        def _parse_retention_days(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        retention_days = _parse_retention_days(d.pop("retentionDays", UNSET))

        def _parse_seats(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        seats = _parse_seats(d.pop("seats", UNSET))

        def _parse_cycle_started_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cycle_started_at = _parse_cycle_started_at(d.pop("cycleStartedAt", UNSET))

        def _parse_trial_ends_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        trial_ends_at = _parse_trial_ends_at(d.pop("trialEndsAt", UNSET))

        billing_usage_response_dto = cls(
            plan=plan,
            used=used,
            subscription_status=subscription_status,
            limit=limit,
            retention_days=retention_days,
            seats=seats,
            cycle_started_at=cycle_started_at,
            trial_ends_at=trial_ends_at,
        )

        billing_usage_response_dto.additional_properties = d
        return billing_usage_response_dto

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
