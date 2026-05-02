from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="EventIngestResponseDto")


@_attrs_define
class EventIngestResponseDto:
    """
    Attributes:
        event_id (str):
        identifier (str):
        dedup_key (str):
        created_at (str):
        queued (bool):
        duplicate (bool | Unset):
        environment_id (None | str | Unset):
    """

    event_id: str
    identifier: str
    dedup_key: str
    created_at: str
    queued: bool
    duplicate: bool | Unset = UNSET
    environment_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        event_id = self.event_id

        identifier = self.identifier

        dedup_key = self.dedup_key

        created_at = self.created_at

        queued = self.queued

        duplicate = self.duplicate

        environment_id: None | str | Unset
        if isinstance(self.environment_id, Unset):
            environment_id = UNSET
        else:
            environment_id = self.environment_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "eventId": event_id,
                "identifier": identifier,
                "dedupKey": dedup_key,
                "createdAt": created_at,
                "queued": queued,
            }
        )
        if duplicate is not UNSET:
            field_dict["duplicate"] = duplicate
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        event_id = d.pop("eventId")

        identifier = d.pop("identifier")

        dedup_key = d.pop("dedupKey")

        created_at = d.pop("createdAt")

        queued = d.pop("queued")

        duplicate = d.pop("duplicate", UNSET)

        def _parse_environment_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        environment_id = _parse_environment_id(d.pop("environmentId", UNSET))

        event_ingest_response_dto = cls(
            event_id=event_id,
            identifier=identifier,
            dedup_key=dedup_key,
            created_at=created_at,
            queued=queued,
            duplicate=duplicate,
            environment_id=environment_id,
        )

        event_ingest_response_dto.additional_properties = d
        return event_ingest_response_dto

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
