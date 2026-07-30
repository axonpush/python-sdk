from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_billing_event_list_item_dto import AdminBillingEventListItemDto


T = TypeVar("T", bound="AdminBillingEventListDto")


@_attrs_define
class AdminBillingEventListDto:
    """
    Attributes:
        events (list[AdminBillingEventListItemDto]):
    """

    events: list[AdminBillingEventListItemDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_billing_event_list_item_dto import AdminBillingEventListItemDto

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.to_dict()
            events.append(events_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "events": events,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_billing_event_list_item_dto import AdminBillingEventListItemDto

        d = dict(src_dict)
        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = AdminBillingEventListItemDto.from_dict(events_item_data)

            events.append(events_item)

        admin_billing_event_list_dto = cls(
            events=events,
        )

        admin_billing_event_list_dto.additional_properties = d
        return admin_billing_event_list_dto

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
