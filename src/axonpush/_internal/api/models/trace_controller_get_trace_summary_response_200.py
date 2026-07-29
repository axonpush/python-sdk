from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="TraceControllerGetTraceSummaryResponse200")


@_attrs_define
class TraceControllerGetTraceSummaryResponse200:
    """
    Attributes:
        trace_id (str):
        event_count (float):
        agents (list[str]):
        event_types (list[str]):
        start_time (datetime.datetime):
        end_time (datetime.datetime):
        duration (float):
        error_count (float):
        tool_call_count (float):
        handoff_count (float):
        total_tokens (float | Unset):
        cost_usd (float | None | Unset): Known reported/estimated cost. Omitted when pricing is unknown.
        status (str | Unset):
    """

    trace_id: str
    event_count: float
    agents: list[str]
    event_types: list[str]
    start_time: datetime.datetime
    end_time: datetime.datetime
    duration: float
    error_count: float
    tool_call_count: float
    handoff_count: float
    total_tokens: float | Unset = UNSET
    cost_usd: float | None | Unset = UNSET
    status: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        trace_id = self.trace_id

        event_count = self.event_count

        agents = self.agents

        event_types = self.event_types

        start_time = self.start_time.isoformat()

        end_time = self.end_time.isoformat()

        duration = self.duration

        error_count = self.error_count

        tool_call_count = self.tool_call_count

        handoff_count = self.handoff_count

        total_tokens = self.total_tokens

        cost_usd: float | None | Unset
        if isinstance(self.cost_usd, Unset):
            cost_usd = UNSET
        else:
            cost_usd = self.cost_usd

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "traceId": trace_id,
                "eventCount": event_count,
                "agents": agents,
                "eventTypes": event_types,
                "startTime": start_time,
                "endTime": end_time,
                "duration": duration,
                "errorCount": error_count,
                "toolCallCount": tool_call_count,
                "handoffCount": handoff_count,
            }
        )
        if total_tokens is not UNSET:
            field_dict["totalTokens"] = total_tokens
        if cost_usd is not UNSET:
            field_dict["costUsd"] = cost_usd
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        trace_id = d.pop("traceId")

        event_count = d.pop("eventCount")

        agents = cast(list[str], d.pop("agents"))

        event_types = cast(list[str], d.pop("eventTypes"))

        start_time = isoparse(d.pop("startTime"))

        end_time = isoparse(d.pop("endTime"))

        duration = d.pop("duration")

        error_count = d.pop("errorCount")

        tool_call_count = d.pop("toolCallCount")

        handoff_count = d.pop("handoffCount")

        total_tokens = d.pop("totalTokens", UNSET)

        def _parse_cost_usd(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        cost_usd = _parse_cost_usd(d.pop("costUsd", UNSET))

        status = d.pop("status", UNSET)

        trace_controller_get_trace_summary_response_200 = cls(
            trace_id=trace_id,
            event_count=event_count,
            agents=agents,
            event_types=event_types,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            error_count=error_count,
            tool_call_count=tool_call_count,
            handoff_count=handoff_count,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            status=status,
        )

        trace_controller_get_trace_summary_response_200.additional_properties = d
        return trace_controller_get_trace_summary_response_200

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
