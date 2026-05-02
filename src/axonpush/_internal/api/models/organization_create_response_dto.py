from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.environment_response_dto import EnvironmentResponseDto
    from ..models.invitation_response_dto import InvitationResponseDto


T = TypeVar("T", bound="OrganizationCreateResponseDto")


@_attrs_define
class OrganizationCreateResponseDto:
    """
    Attributes:
        id (str):
        org_id (str):
        name (str):
        slug (str):
        plan (str):
        sso_enforced (bool):
        events_quota_used_current (float):
        created_at (str):
        access_token (str):
        refresh_token (str):
        description (str | Unset):
        events_quota_monthly (float | Unset):
        retention_days (float | Unset):
        seat_limit (float | Unset):
        lemonsqueezy_subscription_id (str | Unset):
        lemonsqueezy_customer_id (str | Unset):
        sso_connection_id (str | Unset):
        updated_at (str | Unset):
        deleted_at (str | Unset):
        invitations (list[InvitationResponseDto] | Unset):
        environments (list[EnvironmentResponseDto] | Unset):
    """

    id: str
    org_id: str
    name: str
    slug: str
    plan: str
    sso_enforced: bool
    events_quota_used_current: float
    created_at: str
    access_token: str
    refresh_token: str
    description: str | Unset = UNSET
    events_quota_monthly: float | Unset = UNSET
    retention_days: float | Unset = UNSET
    seat_limit: float | Unset = UNSET
    lemonsqueezy_subscription_id: str | Unset = UNSET
    lemonsqueezy_customer_id: str | Unset = UNSET
    sso_connection_id: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    invitations: list[InvitationResponseDto] | Unset = UNSET
    environments: list[EnvironmentResponseDto] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        id = self.id

        org_id = self.org_id

        name = self.name

        slug = self.slug

        plan = self.plan

        sso_enforced = self.sso_enforced

        events_quota_used_current = self.events_quota_used_current

        created_at = self.created_at

        access_token = self.access_token

        refresh_token = self.refresh_token

        description = self.description

        events_quota_monthly = self.events_quota_monthly

        retention_days = self.retention_days

        seat_limit = self.seat_limit

        lemonsqueezy_subscription_id = self.lemonsqueezy_subscription_id

        lemonsqueezy_customer_id = self.lemonsqueezy_customer_id

        sso_connection_id = self.sso_connection_id

        updated_at = self.updated_at

        deleted_at = self.deleted_at

        invitations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.invitations, Unset):
            invitations = []
            for invitations_item_data in self.invitations:
                invitations_item = invitations_item_data.to_dict()
                invitations.append(invitations_item)

        environments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.environments, Unset):
            environments = []
            for environments_item_data in self.environments:
                environments_item = environments_item_data.to_dict()
                environments.append(environments_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "orgId": org_id,
                "name": name,
                "slug": slug,
                "plan": plan,
                "ssoEnforced": sso_enforced,
                "eventsQuotaUsedCurrent": events_quota_used_current,
                "createdAt": created_at,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if events_quota_monthly is not UNSET:
            field_dict["eventsQuotaMonthly"] = events_quota_monthly
        if retention_days is not UNSET:
            field_dict["retentionDays"] = retention_days
        if seat_limit is not UNSET:
            field_dict["seatLimit"] = seat_limit
        if lemonsqueezy_subscription_id is not UNSET:
            field_dict["lemonsqueezySubscriptionId"] = lemonsqueezy_subscription_id
        if lemonsqueezy_customer_id is not UNSET:
            field_dict["lemonsqueezyCustomerId"] = lemonsqueezy_customer_id
        if sso_connection_id is not UNSET:
            field_dict["ssoConnectionId"] = sso_connection_id
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if invitations is not UNSET:
            field_dict["invitations"] = invitations
        if environments is not UNSET:
            field_dict["environments"] = environments

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.environment_response_dto import EnvironmentResponseDto
        from ..models.invitation_response_dto import InvitationResponseDto

        d = dict(src_dict)
        id = d.pop("id")

        org_id = d.pop("orgId")

        name = d.pop("name")

        slug = d.pop("slug")

        plan = d.pop("plan")

        sso_enforced = d.pop("ssoEnforced")

        events_quota_used_current = d.pop("eventsQuotaUsedCurrent")

        created_at = d.pop("createdAt")

        access_token = d.pop("access_token")

        refresh_token = d.pop("refresh_token")

        description = d.pop("description", UNSET)

        events_quota_monthly = d.pop("eventsQuotaMonthly", UNSET)

        retention_days = d.pop("retentionDays", UNSET)

        seat_limit = d.pop("seatLimit", UNSET)

        lemonsqueezy_subscription_id = d.pop("lemonsqueezySubscriptionId", UNSET)

        lemonsqueezy_customer_id = d.pop("lemonsqueezyCustomerId", UNSET)

        sso_connection_id = d.pop("ssoConnectionId", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        _invitations = d.pop("invitations", UNSET)
        invitations: list[InvitationResponseDto] | Unset = UNSET
        if _invitations is not UNSET:
            invitations = []
            for invitations_item_data in _invitations:
                invitations_item = InvitationResponseDto.from_dict(invitations_item_data)

                invitations.append(invitations_item)

        _environments = d.pop("environments", UNSET)
        environments: list[EnvironmentResponseDto] | Unset = UNSET
        if _environments is not UNSET:
            environments = []
            for environments_item_data in _environments:
                environments_item = EnvironmentResponseDto.from_dict(environments_item_data)

                environments.append(environments_item)

        organization_create_response_dto = cls(
            id=id,
            org_id=org_id,
            name=name,
            slug=slug,
            plan=plan,
            sso_enforced=sso_enforced,
            events_quota_used_current=events_quota_used_current,
            created_at=created_at,
            access_token=access_token,
            refresh_token=refresh_token,
            description=description,
            events_quota_monthly=events_quota_monthly,
            retention_days=retention_days,
            seat_limit=seat_limit,
            lemonsqueezy_subscription_id=lemonsqueezy_subscription_id,
            lemonsqueezy_customer_id=lemonsqueezy_customer_id,
            sso_connection_id=sso_connection_id,
            updated_at=updated_at,
            deleted_at=deleted_at,
            invitations=invitations,
            environments=environments,
        )

        organization_create_response_dto.additional_properties = d
        return organization_create_response_dto

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
