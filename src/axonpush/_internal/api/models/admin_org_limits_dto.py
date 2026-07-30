from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_org_limit_dto import AdminOrgLimitDto


T = TypeVar("T", bound="AdminOrgLimitsDto")


@_attrs_define
class AdminOrgLimitsDto:
    """
    Attributes:
        seats (AdminOrgLimitDto):
        retention_days (AdminOrgLimitDto):
        events_quota_monthly (AdminOrgLimitDto):
    """

    seats: AdminOrgLimitDto
    retention_days: AdminOrgLimitDto
    events_quota_monthly: AdminOrgLimitDto
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_org_limit_dto import AdminOrgLimitDto

        seats = self.seats.to_dict()

        retention_days = self.retention_days.to_dict()

        events_quota_monthly = self.events_quota_monthly.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "seats": seats,
                "retentionDays": retention_days,
                "eventsQuotaMonthly": events_quota_monthly,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_org_limit_dto import AdminOrgLimitDto

        d = dict(src_dict)
        seats = AdminOrgLimitDto.from_dict(d.pop("seats"))

        retention_days = AdminOrgLimitDto.from_dict(d.pop("retentionDays"))

        events_quota_monthly = AdminOrgLimitDto.from_dict(d.pop("eventsQuotaMonthly"))

        admin_org_limits_dto = cls(
            seats=seats,
            retention_days=retention_days,
            events_quota_monthly=events_quota_monthly,
        )

        admin_org_limits_dto.additional_properties = d
        return admin_org_limits_dto

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
