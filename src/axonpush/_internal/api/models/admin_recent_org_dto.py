from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminRecentOrgDto")


@_attrs_define
class AdminRecentOrgDto:
    """
    Attributes:
        org_id (str):
        name (str):
        slug (str):
        plan (str):
        subscription_status (None | str):
        created_at (str):
    """

    org_id: str
    name: str
    slug: str
    plan: str
    subscription_status: None | str
    created_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        name = self.name

        slug = self.slug

        plan = self.plan

        subscription_status: None | str
        subscription_status = self.subscription_status

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

        created_at = d.pop("createdAt")

        admin_recent_org_dto = cls(
            org_id=org_id,
            name=name,
            slug=slug,
            plan=plan,
            subscription_status=subscription_status,
            created_at=created_at,
        )

        admin_recent_org_dto.additional_properties = d
        return admin_recent_org_dto

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
