from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.webhook_delivery_response_dto_status import WebhookDeliveryResponseDtoStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="WebhookDeliveryResponseDto")


@_attrs_define
class WebhookDeliveryResponseDto:
    """
    Attributes:
        id (str):
        delivery_id (str):
        endpoint_id (str):
        event_id (str):
        status (WebhookDeliveryResponseDtoStatus):
        attempts (float):
        created_at (str):
        status_code (float | Unset):
        response_body (str | Unset):
        last_attempt_at (str | Unset):
        next_attempt_at (str | Unset):
        error (str | Unset):
    """

    id: str
    delivery_id: str
    endpoint_id: str
    event_id: str
    status: WebhookDeliveryResponseDtoStatus
    attempts: float
    created_at: str
    status_code: float | Unset = UNSET
    response_body: str | Unset = UNSET
    last_attempt_at: str | Unset = UNSET
    next_attempt_at: str | Unset = UNSET
    error: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        delivery_id = self.delivery_id

        endpoint_id = self.endpoint_id

        event_id = self.event_id

        status = self.status.value

        attempts = self.attempts

        created_at = self.created_at

        status_code = self.status_code

        response_body = self.response_body

        last_attempt_at = self.last_attempt_at

        next_attempt_at = self.next_attempt_at

        error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "deliveryId": delivery_id,
                "endpointId": endpoint_id,
                "eventId": event_id,
                "status": status,
                "attempts": attempts,
                "createdAt": created_at,
            }
        )
        if status_code is not UNSET:
            field_dict["statusCode"] = status_code
        if response_body is not UNSET:
            field_dict["responseBody"] = response_body
        if last_attempt_at is not UNSET:
            field_dict["lastAttemptAt"] = last_attempt_at
        if next_attempt_at is not UNSET:
            field_dict["nextAttemptAt"] = next_attempt_at
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        delivery_id = d.pop("deliveryId")

        endpoint_id = d.pop("endpointId")

        event_id = d.pop("eventId")

        status = WebhookDeliveryResponseDtoStatus(d.pop("status"))

        attempts = d.pop("attempts")

        created_at = d.pop("createdAt")

        status_code = d.pop("statusCode", UNSET)

        response_body = d.pop("responseBody", UNSET)

        last_attempt_at = d.pop("lastAttemptAt", UNSET)

        next_attempt_at = d.pop("nextAttemptAt", UNSET)

        error = d.pop("error", UNSET)

        webhook_delivery_response_dto = cls(
            id=id,
            delivery_id=delivery_id,
            endpoint_id=endpoint_id,
            event_id=event_id,
            status=status,
            attempts=attempts,
            created_at=created_at,
            status_code=status_code,
            response_body=response_body,
            last_attempt_at=last_attempt_at,
            next_attempt_at=next_attempt_at,
            error=error,
        )

        webhook_delivery_response_dto.additional_properties = d
        return webhook_delivery_response_dto

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
