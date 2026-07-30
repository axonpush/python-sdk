from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_export_destination_dto_signals import UpdateExportDestinationDtoSignals
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_export_destination_dto_headers import UpdateExportDestinationDtoHeaders


T = TypeVar("T", bound="UpdateExportDestinationDto")


@_attrs_define
class UpdateExportDestinationDto:
    """
    Attributes:
        name (str | Unset):
        endpoint_url (str | Unset):
        headers (UpdateExportDestinationDtoHeaders | Unset): Replaces the stored header map. Never returned by the API.
        signals (UpdateExportDestinationDtoSignals | Unset):
        event_type_filter (list[str] | Unset):
        service_name (str | Unset):
        active (bool | Unset):
    """

    name: str | Unset = UNSET
    endpoint_url: str | Unset = UNSET
    headers: UpdateExportDestinationDtoHeaders | Unset = UNSET
    signals: UpdateExportDestinationDtoSignals | Unset = UNSET
    event_type_filter: list[str] | Unset = UNSET
    service_name: str | Unset = UNSET
    active: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_export_destination_dto_headers import UpdateExportDestinationDtoHeaders

        name = self.name

        endpoint_url = self.endpoint_url

        headers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.headers, Unset):
            headers = self.headers.to_dict()

        signals: str | Unset = UNSET
        if not isinstance(self.signals, Unset):
            signals = self.signals.value

        event_type_filter: list[str] | Unset = UNSET
        if not isinstance(self.event_type_filter, Unset):
            event_type_filter = self.event_type_filter

        service_name = self.service_name

        active = self.active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if endpoint_url is not UNSET:
            field_dict["endpointUrl"] = endpoint_url
        if headers is not UNSET:
            field_dict["headers"] = headers
        if signals is not UNSET:
            field_dict["signals"] = signals
        if event_type_filter is not UNSET:
            field_dict["eventTypeFilter"] = event_type_filter
        if service_name is not UNSET:
            field_dict["serviceName"] = service_name
        if active is not UNSET:
            field_dict["active"] = active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_export_destination_dto_headers import UpdateExportDestinationDtoHeaders

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        endpoint_url = d.pop("endpointUrl", UNSET)

        _headers = d.pop("headers", UNSET)
        headers: UpdateExportDestinationDtoHeaders | Unset
        if isinstance(_headers, Unset):
            headers = UNSET
        else:
            headers = UpdateExportDestinationDtoHeaders.from_dict(_headers)

        _signals = d.pop("signals", UNSET)
        signals: UpdateExportDestinationDtoSignals | Unset
        if isinstance(_signals, Unset):
            signals = UNSET
        else:
            signals = UpdateExportDestinationDtoSignals(_signals)

        event_type_filter = cast(list[str], d.pop("eventTypeFilter", UNSET))

        service_name = d.pop("serviceName", UNSET)

        active = d.pop("active", UNSET)

        update_export_destination_dto = cls(
            name=name,
            endpoint_url=endpoint_url,
            headers=headers,
            signals=signals,
            event_type_filter=event_type_filter,
            service_name=service_name,
            active=active,
        )

        update_export_destination_dto.additional_properties = d
        return update_export_destination_dto

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
