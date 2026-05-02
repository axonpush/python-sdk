from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceControllerGetDashboardStatsResponse200EventsByHourItem")


@_attrs_define
class TraceControllerGetDashboardStatsResponse200EventsByHourItem:
    """
    Attributes:
        hour (datetime.datetime | Unset):
        count (float | Unset):
    """

    hour: datetime.datetime | Unset = UNSET
    count: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hour: str | Unset = UNSET
        if not isinstance(self.hour, Unset):
            hour = self.hour.isoformat()

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if hour is not UNSET:
            field_dict["hour"] = hour
        if count is not UNSET:
            field_dict["count"] = count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _hour = d.pop("hour", UNSET)
        hour: datetime.datetime | Unset
        if isinstance(_hour, Unset):
            hour = UNSET
        else:
            hour = isoparse(_hour)

        count = d.pop("count", UNSET)

        trace_controller_get_dashboard_stats_response_200_events_by_hour_item = cls(
            hour=hour,
            count=count,
        )

        trace_controller_get_dashboard_stats_response_200_events_by_hour_item.additional_properties = d
        return trace_controller_get_dashboard_stats_response_200_events_by_hour_item

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
