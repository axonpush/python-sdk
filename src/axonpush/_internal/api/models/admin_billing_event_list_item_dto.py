from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminBillingEventListItemDto")


@_attrs_define
class AdminBillingEventListItemDto:
    """
    Attributes:
        id (str):
        org_id (str):
        external_id (str):
        event_name (str):
        created_at (str):
        processed_at (None | str):
        error (None | str):
    """

    id: str
    org_id: str
    external_id: str
    event_name: str
    created_at: str
    processed_at: None | str
    error: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        org_id = self.org_id

        external_id = self.external_id

        event_name = self.event_name

        created_at = self.created_at

        processed_at: None | str
        processed_at = self.processed_at

        error: None | str
        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "orgId": org_id,
                "externalId": external_id,
                "eventName": event_name,
                "createdAt": created_at,
                "processedAt": processed_at,
                "error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        org_id = d.pop("orgId")

        external_id = d.pop("externalId")

        event_name = d.pop("eventName")

        created_at = d.pop("createdAt")

        def _parse_processed_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        processed_at = _parse_processed_at(d.pop("processedAt"))

        def _parse_error(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        error = _parse_error(d.pop("error"))

        admin_billing_event_list_item_dto = cls(
            id=id,
            org_id=org_id,
            external_id=external_id,
            event_name=event_name,
            created_at=created_at,
            processed_at=processed_at,
            error=error,
        )

        admin_billing_event_list_item_dto.additional_properties = d
        return admin_billing_event_list_item_dto

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
