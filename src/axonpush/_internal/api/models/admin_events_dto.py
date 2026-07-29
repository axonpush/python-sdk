from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminEventsDto")


@_attrs_define
class AdminEventsDto:
    """
    Attributes:
        total (float): All-time events ingested (sum of per-org events_total counters)
        today (float): Events ingested today (UTC)
        this_cycle (float): Sum of every org’s events used in its current billing cycle
    """

    total: float
    today: float
    this_cycle: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        today = self.today

        this_cycle = self.this_cycle

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "today": today,
                "thisCycle": this_cycle,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total = d.pop("total")

        today = d.pop("today")

        this_cycle = d.pop("thisCycle")

        admin_events_dto = cls(
            total=total,
            today=today,
            this_cycle=this_cycle,
        )

        admin_events_dto.additional_properties = d
        return admin_events_dto

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
