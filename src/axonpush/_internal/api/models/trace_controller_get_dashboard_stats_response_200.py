from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.trace_controller_get_dashboard_stats_response_200_events_by_hour_item import (
        TraceControllerGetDashboardStatsResponse200EventsByHourItem,
    )


T = TypeVar("T", bound="TraceControllerGetDashboardStatsResponse200")


@_attrs_define
class TraceControllerGetDashboardStatsResponse200:
    """
    Attributes:
        total_events (float):
        events_today (float):
        total_traces (float):
        traces_today (float):
        error_count (float):
        error_rate (float):
        avg_trace_duration (float):
        events_by_hour (list[TraceControllerGetDashboardStatsResponse200EventsByHourItem]):
    """

    total_events: float
    events_today: float
    total_traces: float
    traces_today: float
    error_count: float
    error_rate: float
    avg_trace_duration: float
    events_by_hour: list[TraceControllerGetDashboardStatsResponse200EventsByHourItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trace_controller_get_dashboard_stats_response_200_events_by_hour_item import (
            TraceControllerGetDashboardStatsResponse200EventsByHourItem,
        )

        total_events = self.total_events

        events_today = self.events_today

        total_traces = self.total_traces

        traces_today = self.traces_today

        error_count = self.error_count

        error_rate = self.error_rate

        avg_trace_duration = self.avg_trace_duration

        events_by_hour = []
        for events_by_hour_item_data in self.events_by_hour:
            events_by_hour_item = events_by_hour_item_data.to_dict()
            events_by_hour.append(events_by_hour_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "totalEvents": total_events,
                "eventsToday": events_today,
                "totalTraces": total_traces,
                "tracesToday": traces_today,
                "errorCount": error_count,
                "errorRate": error_rate,
                "avgTraceDuration": avg_trace_duration,
                "eventsByHour": events_by_hour,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_controller_get_dashboard_stats_response_200_events_by_hour_item import (
            TraceControllerGetDashboardStatsResponse200EventsByHourItem,
        )

        d = dict(src_dict)
        total_events = d.pop("totalEvents")

        events_today = d.pop("eventsToday")

        total_traces = d.pop("totalTraces")

        traces_today = d.pop("tracesToday")

        error_count = d.pop("errorCount")

        error_rate = d.pop("errorRate")

        avg_trace_duration = d.pop("avgTraceDuration")

        events_by_hour = []
        _events_by_hour = d.pop("eventsByHour")
        for events_by_hour_item_data in _events_by_hour:
            events_by_hour_item = (
                TraceControllerGetDashboardStatsResponse200EventsByHourItem.from_dict(
                    events_by_hour_item_data
                )
            )

            events_by_hour.append(events_by_hour_item)

        trace_controller_get_dashboard_stats_response_200 = cls(
            total_events=total_events,
            events_today=events_today,
            total_traces=total_traces,
            traces_today=traces_today,
            error_count=error_count,
            error_rate=error_rate,
            avg_trace_duration=avg_trace_duration,
            events_by_hour=events_by_hour,
        )

        trace_controller_get_dashboard_stats_response_200.additional_properties = d
        return trace_controller_get_dashboard_stats_response_200

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
