from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BillingWebhookResponseDto")


@_attrs_define
class BillingWebhookResponseDto:
    """
    Attributes:
        ok (bool):
        deduped (bool | Unset):
        skipped (str | Unset):
        enqueued_retry (bool | Unset):
    """

    ok: bool
    deduped: bool | Unset = UNSET
    skipped: str | Unset = UNSET
    enqueued_retry: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ok = self.ok

        deduped = self.deduped

        skipped = self.skipped

        enqueued_retry = self.enqueued_retry

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ok": ok,
            }
        )
        if deduped is not UNSET:
            field_dict["deduped"] = deduped
        if skipped is not UNSET:
            field_dict["skipped"] = skipped
        if enqueued_retry is not UNSET:
            field_dict["enqueuedRetry"] = enqueued_retry

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ok = d.pop("ok")

        deduped = d.pop("deduped", UNSET)

        skipped = d.pop("skipped", UNSET)

        enqueued_retry = d.pop("enqueuedRetry", UNSET)

        billing_webhook_response_dto = cls(
            ok=ok,
            deduped=deduped,
            skipped=skipped,
            enqueued_retry=enqueued_retry,
        )

        billing_webhook_response_dto.additional_properties = d
        return billing_webhook_response_dto

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
