from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ExportDestinationResponseDto")


@_attrs_define
class ExportDestinationResponseDto:
    """
    Attributes:
        id (str):
        destination_id (str):
        org_id (str):
        env_slug (str):
        name (str):
        endpoint_url (str):
        signals (list[str]): OTLP signals: logs and/or traces
        header_keys (list[str]): Configured header names (values are masked)
        active (bool):
        created_at (str):
        event_type_filter (list[str] | Unset):
        service_name (str | Unset):
        updated_at (str | Unset):
    """

    id: str
    destination_id: str
    org_id: str
    env_slug: str
    name: str
    endpoint_url: str
    signals: list[str]
    header_keys: list[str]
    active: bool
    created_at: str
    event_type_filter: list[str] | Unset = UNSET
    service_name: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        destination_id = self.destination_id

        org_id = self.org_id

        env_slug = self.env_slug

        name = self.name

        endpoint_url = self.endpoint_url

        signals = self.signals

        header_keys = self.header_keys

        active = self.active

        created_at = self.created_at

        event_type_filter: list[str] | Unset = UNSET
        if not isinstance(self.event_type_filter, Unset):
            event_type_filter = self.event_type_filter

        service_name = self.service_name

        updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "destinationId": destination_id,
                "orgId": org_id,
                "envSlug": env_slug,
                "name": name,
                "endpointUrl": endpoint_url,
                "signals": signals,
                "headerKeys": header_keys,
                "active": active,
                "createdAt": created_at,
            }
        )
        if event_type_filter is not UNSET:
            field_dict["eventTypeFilter"] = event_type_filter
        if service_name is not UNSET:
            field_dict["serviceName"] = service_name
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        destination_id = d.pop("destinationId")

        org_id = d.pop("orgId")

        env_slug = d.pop("envSlug")

        name = d.pop("name")

        endpoint_url = d.pop("endpointUrl")

        signals = cast(list[str], d.pop("signals"))

        header_keys = cast(list[str], d.pop("headerKeys"))

        active = d.pop("active")

        created_at = d.pop("createdAt")

        event_type_filter = cast(list[str], d.pop("eventTypeFilter", UNSET))

        service_name = d.pop("serviceName", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        export_destination_response_dto = cls(
            id=id,
            destination_id=destination_id,
            org_id=org_id,
            env_slug=env_slug,
            name=name,
            endpoint_url=endpoint_url,
            signals=signals,
            header_keys=header_keys,
            active=active,
            created_at=created_at,
            event_type_filter=event_type_filter,
            service_name=service_name,
            updated_at=updated_at,
        )

        export_destination_response_dto.additional_properties = d
        return export_destination_response_dto

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
