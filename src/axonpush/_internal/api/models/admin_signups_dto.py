from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_recent_org_dto import AdminRecentOrgDto
    from ..models.admin_recent_user_dto import AdminRecentUserDto
    from ..models.admin_signup_point_dto import AdminSignupPointDto


T = TypeVar("T", bound="AdminSignupsDto")


@_attrs_define
class AdminSignupsDto:
    """
    Attributes:
        recent_orgs (list[AdminRecentOrgDto]):
        recent_users (list[AdminRecentUserDto]):
        series (list[AdminSignupPointDto]): Signups per UTC day
    """

    recent_orgs: list[AdminRecentOrgDto]
    recent_users: list[AdminRecentUserDto]
    series: list[AdminSignupPointDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_recent_org_dto import AdminRecentOrgDto
        from ..models.admin_recent_user_dto import AdminRecentUserDto
        from ..models.admin_signup_point_dto import AdminSignupPointDto

        recent_orgs = []
        for recent_orgs_item_data in self.recent_orgs:
            recent_orgs_item = recent_orgs_item_data.to_dict()
            recent_orgs.append(recent_orgs_item)

        recent_users = []
        for recent_users_item_data in self.recent_users:
            recent_users_item = recent_users_item_data.to_dict()
            recent_users.append(recent_users_item)

        series = []
        for series_item_data in self.series:
            series_item = series_item_data.to_dict()
            series.append(series_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "recentOrgs": recent_orgs,
                "recentUsers": recent_users,
                "series": series,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_recent_org_dto import AdminRecentOrgDto
        from ..models.admin_recent_user_dto import AdminRecentUserDto
        from ..models.admin_signup_point_dto import AdminSignupPointDto

        d = dict(src_dict)
        recent_orgs = []
        _recent_orgs = d.pop("recentOrgs")
        for recent_orgs_item_data in _recent_orgs:
            recent_orgs_item = AdminRecentOrgDto.from_dict(recent_orgs_item_data)

            recent_orgs.append(recent_orgs_item)

        recent_users = []
        _recent_users = d.pop("recentUsers")
        for recent_users_item_data in _recent_users:
            recent_users_item = AdminRecentUserDto.from_dict(recent_users_item_data)

            recent_users.append(recent_users_item)

        series = []
        _series = d.pop("series")
        for series_item_data in _series:
            series_item = AdminSignupPointDto.from_dict(series_item_data)

            series.append(series_item)

        admin_signups_dto = cls(
            recent_orgs=recent_orgs,
            recent_users=recent_users,
            series=series,
        )

        admin_signups_dto.additional_properties = d
        return admin_signups_dto

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
