from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReleaseResponseDto")


@_attrs_define
class ReleaseResponseDto:
    """
    Attributes:
        org_id (str):
        version (str):
        date_created (str):
        projects (str | Unset):
        date_released (str | Unset):
        first_event_at (str | Unset):
        last_event_at (str | Unset):
    """

    org_id: str
    version: str
    date_created: str
    projects: str | Unset = UNSET
    date_released: str | Unset = UNSET
    first_event_at: str | Unset = UNSET
    last_event_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        version = self.version

        date_created = self.date_created

        projects = self.projects

        date_released = self.date_released

        first_event_at = self.first_event_at

        last_event_at = self.last_event_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orgId": org_id,
                "version": version,
                "dateCreated": date_created,
            }
        )
        if projects is not UNSET:
            field_dict["projects"] = projects
        if date_released is not UNSET:
            field_dict["dateReleased"] = date_released
        if first_event_at is not UNSET:
            field_dict["firstEventAt"] = first_event_at
        if last_event_at is not UNSET:
            field_dict["lastEventAt"] = last_event_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("orgId")

        version = d.pop("version")

        date_created = d.pop("dateCreated")

        projects = d.pop("projects", UNSET)

        date_released = d.pop("dateReleased", UNSET)

        first_event_at = d.pop("firstEventAt", UNSET)

        last_event_at = d.pop("lastEventAt", UNSET)

        release_response_dto = cls(
            org_id=org_id,
            version=version,
            date_created=date_created,
            projects=projects,
            date_released=date_released,
            first_event_at=first_event_at,
            last_event_at=last_event_at,
        )

        release_response_dto.additional_properties = d
        return release_response_dto

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
