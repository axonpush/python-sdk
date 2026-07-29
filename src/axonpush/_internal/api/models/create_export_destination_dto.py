from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_export_destination_dto_signals import CreateExportDestinationDtoSignals
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_export_destination_dto_headers import CreateExportDestinationDtoHeaders


T = TypeVar("T", bound="CreateExportDestinationDto")


@_attrs_define
class CreateExportDestinationDto:
    """
    Attributes:
        name (str):
        env_slug (str): Environment slug this destination is scoped to (e.g. "prod")
        endpoint_url (str): OTLP/HTTP base URL (v1/logs and v1/traces are appended)
        signals (CreateExportDestinationDtoSignals):
        headers (CreateExportDestinationDtoHeaders | Unset): Header name -> value map (e.g. DD-API-KEY). Stored server-
            side, never returned.
        event_type_filter (list[str] | Unset): Allow-list of event types to export (empty = all types)
        service_name (str | Unset): service.name attribute stamped on exported resources
        active (bool | Unset):  Default: True.
    """

    name: str
    env_slug: str
    endpoint_url: str
    signals: CreateExportDestinationDtoSignals
    headers: CreateExportDestinationDtoHeaders | Unset = UNSET
    event_type_filter: list[str] | Unset = UNSET
    service_name: str | Unset = UNSET
    active: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_export_destination_dto_headers import CreateExportDestinationDtoHeaders

        name = self.name

        env_slug = self.env_slug

        endpoint_url = self.endpoint_url

        signals = self.signals.value

        headers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.headers, Unset):
            headers = self.headers.to_dict()

        event_type_filter: list[str] | Unset = UNSET
        if not isinstance(self.event_type_filter, Unset):
            event_type_filter = self.event_type_filter

        service_name = self.service_name

        active = self.active

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "envSlug": env_slug,
                "endpointUrl": endpoint_url,
                "signals": signals,
            }
        )
        if headers is not UNSET:
            field_dict["headers"] = headers
        if event_type_filter is not UNSET:
            field_dict["eventTypeFilter"] = event_type_filter
        if service_name is not UNSET:
            field_dict["serviceName"] = service_name
        if active is not UNSET:
            field_dict["active"] = active

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_export_destination_dto_headers import CreateExportDestinationDtoHeaders

        d = dict(src_dict)
        name = d.pop("name")

        env_slug = d.pop("envSlug")

        endpoint_url = d.pop("endpointUrl")

        signals = CreateExportDestinationDtoSignals(d.pop("signals"))

        _headers = d.pop("headers", UNSET)
        headers: CreateExportDestinationDtoHeaders | Unset
        if isinstance(_headers, Unset):
            headers = UNSET
        else:
            headers = CreateExportDestinationDtoHeaders.from_dict(_headers)

        event_type_filter = cast(list[str], d.pop("eventTypeFilter", UNSET))

        service_name = d.pop("serviceName", UNSET)

        active = d.pop("active", UNSET)

        create_export_destination_dto = cls(
            name=name,
            env_slug=env_slug,
            endpoint_url=endpoint_url,
            signals=signals,
            headers=headers,
            event_type_filter=event_type_filter,
            service_name=service_name,
            active=active,
        )

        create_export_destination_dto.additional_properties = d
        return create_export_destination_dto

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
