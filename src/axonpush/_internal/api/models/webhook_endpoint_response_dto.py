from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookEndpointResponseDto")


@_attrs_define
class WebhookEndpointResponseDto:
    """
    Attributes:
        id (str):
        endpoint_id (str):
        channel_id (str):
        url (str):
        is_active (bool):
        created_at (str):
        org_id (str | Unset):
        event_types (list[str] | Unset):
        signing_secret_prefix (str | Unset):
        has_secret (bool | Unset):
        description (str | Unset):
        updated_at (str | Unset):
        deleted_at (str | Unset):
    """

    id: str
    endpoint_id: str
    channel_id: str
    url: str
    is_active: bool
    created_at: str
    org_id: str | Unset = UNSET
    event_types: list[str] | Unset = UNSET
    signing_secret_prefix: str | Unset = UNSET
    has_secret: bool | Unset = UNSET
    description: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        endpoint_id = self.endpoint_id

        channel_id = self.channel_id

        url = self.url

        is_active = self.is_active

        created_at = self.created_at

        org_id = self.org_id

        event_types: list[str] | Unset = UNSET
        if not isinstance(self.event_types, Unset):
            event_types = self.event_types

        signing_secret_prefix = self.signing_secret_prefix

        has_secret = self.has_secret

        description = self.description

        updated_at = self.updated_at

        deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "endpointId": endpoint_id,
                "channelId": channel_id,
                "url": url,
                "isActive": is_active,
                "createdAt": created_at,
            }
        )
        if org_id is not UNSET:
            field_dict["orgId"] = org_id
        if event_types is not UNSET:
            field_dict["eventTypes"] = event_types
        if signing_secret_prefix is not UNSET:
            field_dict["signingSecretPrefix"] = signing_secret_prefix
        if has_secret is not UNSET:
            field_dict["hasSecret"] = has_secret
        if description is not UNSET:
            field_dict["description"] = description
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        endpoint_id = d.pop("endpointId")

        channel_id = d.pop("channelId")

        url = d.pop("url")

        is_active = d.pop("isActive")

        created_at = d.pop("createdAt")

        org_id = d.pop("orgId", UNSET)

        event_types = cast(list[str], d.pop("eventTypes", UNSET))

        signing_secret_prefix = d.pop("signingSecretPrefix", UNSET)

        has_secret = d.pop("hasSecret", UNSET)

        description = d.pop("description", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        webhook_endpoint_response_dto = cls(
            id=id,
            endpoint_id=endpoint_id,
            channel_id=channel_id,
            url=url,
            is_active=is_active,
            created_at=created_at,
            org_id=org_id,
            event_types=event_types,
            signing_secret_prefix=signing_secret_prefix,
            has_secret=has_secret,
            description=description,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        webhook_endpoint_response_dto.additional_properties = d
        return webhook_endpoint_response_dto

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
