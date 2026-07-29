from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminOrgListItemDto")


@_attrs_define
class AdminOrgListItemDto:
    """
    Attributes:
        org_id (str):
        name (str):
        slug (str):
        plan (str):
        subscription_status (None | str):
        events_quota_used_current (float | None):
        events_quota_monthly (float | None):
        seat_limit (float | None):
        billing_monthly_amount_usd (float | None):
        billing_notes (None | str):
        trial_ends_at (None | str):
        created_at (str):
    """

    org_id: str
    name: str
    slug: str
    plan: str
    subscription_status: None | str
    events_quota_used_current: float | None
    events_quota_monthly: float | None
    seat_limit: float | None
    billing_monthly_amount_usd: float | None
    billing_notes: None | str
    trial_ends_at: None | str
    created_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        name = self.name

        slug = self.slug

        plan = self.plan

        subscription_status: None | str
        subscription_status = self.subscription_status

        events_quota_used_current: float | None
        events_quota_used_current = self.events_quota_used_current

        events_quota_monthly: float | None
        events_quota_monthly = self.events_quota_monthly

        seat_limit: float | None
        seat_limit = self.seat_limit

        billing_monthly_amount_usd: float | None
        billing_monthly_amount_usd = self.billing_monthly_amount_usd

        billing_notes: None | str
        billing_notes = self.billing_notes

        trial_ends_at: None | str
        trial_ends_at = self.trial_ends_at

        created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orgId": org_id,
                "name": name,
                "slug": slug,
                "plan": plan,
                "subscriptionStatus": subscription_status,
                "eventsQuotaUsedCurrent": events_quota_used_current,
                "eventsQuotaMonthly": events_quota_monthly,
                "seatLimit": seat_limit,
                "billingMonthlyAmountUsd": billing_monthly_amount_usd,
                "billingNotes": billing_notes,
                "trialEndsAt": trial_ends_at,
                "createdAt": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("orgId")

        name = d.pop("name")

        slug = d.pop("slug")

        plan = d.pop("plan")

        def _parse_subscription_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        subscription_status = _parse_subscription_status(d.pop("subscriptionStatus"))

        def _parse_events_quota_used_current(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        events_quota_used_current = _parse_events_quota_used_current(
            d.pop("eventsQuotaUsedCurrent")
        )

        def _parse_events_quota_monthly(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        events_quota_monthly = _parse_events_quota_monthly(d.pop("eventsQuotaMonthly"))

        def _parse_seat_limit(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        seat_limit = _parse_seat_limit(d.pop("seatLimit"))

        def _parse_billing_monthly_amount_usd(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        billing_monthly_amount_usd = _parse_billing_monthly_amount_usd(
            d.pop("billingMonthlyAmountUsd")
        )

        def _parse_billing_notes(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        billing_notes = _parse_billing_notes(d.pop("billingNotes"))

        def _parse_trial_ends_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trial_ends_at = _parse_trial_ends_at(d.pop("trialEndsAt"))

        created_at = d.pop("createdAt")

        admin_org_list_item_dto = cls(
            org_id=org_id,
            name=name,
            slug=slug,
            plan=plan,
            subscription_status=subscription_status,
            events_quota_used_current=events_quota_used_current,
            events_quota_monthly=events_quota_monthly,
            seat_limit=seat_limit,
            billing_monthly_amount_usd=billing_monthly_amount_usd,
            billing_notes=billing_notes,
            trial_ends_at=trial_ends_at,
            created_at=created_at,
        )

        admin_org_list_item_dto.additional_properties = d
        return admin_org_list_item_dto

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
