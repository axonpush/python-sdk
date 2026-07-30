from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminUserListItemDto")


@_attrs_define
class AdminUserListItemDto:
    """
    Attributes:
        user_id (str):
        email (str):
        first_name (None | str):
        last_name (None | str):
        organization_id (None | str):
        disabled_at (None | str):
        created_at (str):
        trial_started_at (None | str):
        trial_ends_at (None | str):
    """

    user_id: str
    email: str
    first_name: None | str
    last_name: None | str
    organization_id: None | str
    disabled_at: None | str
    created_at: str
    trial_started_at: None | str
    trial_ends_at: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        email = self.email

        first_name: None | str
        first_name = self.first_name

        last_name: None | str
        last_name = self.last_name

        organization_id: None | str
        organization_id = self.organization_id

        disabled_at: None | str
        disabled_at = self.disabled_at

        created_at = self.created_at

        trial_started_at: None | str
        trial_started_at = self.trial_started_at

        trial_ends_at: None | str
        trial_ends_at = self.trial_ends_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "userId": user_id,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "organizationId": organization_id,
                "disabledAt": disabled_at,
                "createdAt": created_at,
                "trialStartedAt": trial_started_at,
                "trialEndsAt": trial_ends_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("userId")

        email = d.pop("email")

        def _parse_first_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        first_name = _parse_first_name(d.pop("firstName"))

        def _parse_last_name(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_name = _parse_last_name(d.pop("lastName"))

        def _parse_organization_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        organization_id = _parse_organization_id(d.pop("organizationId"))

        def _parse_disabled_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        disabled_at = _parse_disabled_at(d.pop("disabledAt"))

        created_at = d.pop("createdAt")

        def _parse_trial_started_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trial_started_at = _parse_trial_started_at(d.pop("trialStartedAt"))

        def _parse_trial_ends_at(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trial_ends_at = _parse_trial_ends_at(d.pop("trialEndsAt"))

        admin_user_list_item_dto = cls(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization_id=organization_id,
            disabled_at=disabled_at,
            created_at=created_at,
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
        )

        admin_user_list_item_dto.additional_properties = d
        return admin_user_list_item_dto

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
