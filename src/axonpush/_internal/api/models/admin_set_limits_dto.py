from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminSetLimitsDto")


@_attrs_define
class AdminSetLimitsDto:
    """
    Attributes:
        seat_limit (float | None | Unset): Seat limit override: >=1 for a value, -1 for unlimited, null to clear
        retention_days (float | None | Unset): Retention days override: >=1 for a value, -1 for unlimited, null to clear
        events_quota_monthly (float | None | Unset): Monthly events quota override: >=0 for a value, -1 for unlimited,
            null to clear
    """

    seat_limit: float | None | Unset = UNSET
    retention_days: float | None | Unset = UNSET
    events_quota_monthly: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        seat_limit: float | None | Unset
        if isinstance(self.seat_limit, Unset):
            seat_limit = UNSET
        else:
            seat_limit = self.seat_limit

        retention_days: float | None | Unset
        if isinstance(self.retention_days, Unset):
            retention_days = UNSET
        else:
            retention_days = self.retention_days

        events_quota_monthly: float | None | Unset
        if isinstance(self.events_quota_monthly, Unset):
            events_quota_monthly = UNSET
        else:
            events_quota_monthly = self.events_quota_monthly

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if seat_limit is not UNSET:
            field_dict["seatLimit"] = seat_limit
        if retention_days is not UNSET:
            field_dict["retentionDays"] = retention_days
        if events_quota_monthly is not UNSET:
            field_dict["eventsQuotaMonthly"] = events_quota_monthly

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_seat_limit(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        seat_limit = _parse_seat_limit(d.pop("seatLimit", UNSET))

        def _parse_retention_days(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        retention_days = _parse_retention_days(d.pop("retentionDays", UNSET))

        def _parse_events_quota_monthly(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        events_quota_monthly = _parse_events_quota_monthly(d.pop("eventsQuotaMonthly", UNSET))

        admin_set_limits_dto = cls(
            seat_limit=seat_limit,
            retention_days=retention_days,
            events_quota_monthly=events_quota_monthly,
        )

        admin_set_limits_dto.additional_properties = d
        return admin_set_limits_dto

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
