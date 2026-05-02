from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.app_response_dto import AppResponseDto


T = TypeVar("T", bound="ChannelResponseDto")


@_attrs_define
class ChannelResponseDto:
    """
    Attributes:
        id (str):
        channel_id (str):
        org_id (str):
        app_id (str):
        name (str):
        created_at (str):
        updated_at (str | Unset):
        deleted_at (str | Unset):
        app (AppResponseDto | Unset):
    """

    id: str
    channel_id: str
    org_id: str
    app_id: str
    name: str
    created_at: str
    updated_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    app: AppResponseDto | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        id = self.id

        channel_id = self.channel_id

        org_id = self.org_id

        app_id = self.app_id

        name = self.name

        created_at = self.created_at

        updated_at = self.updated_at

        deleted_at = self.deleted_at

        app: dict[str, Any] | Unset = UNSET
        if not isinstance(self.app, Unset):
            app = self.app.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "channelId": channel_id,
                "orgId": org_id,
                "appId": app_id,
                "name": name,
                "createdAt": created_at,
            }
        )
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if app is not UNSET:
            field_dict["app"] = app

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_response_dto import AppResponseDto

        d = dict(src_dict)
        id = d.pop("id")

        channel_id = d.pop("channelId")

        org_id = d.pop("orgId")

        app_id = d.pop("appId")

        name = d.pop("name")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        _app = d.pop("app", UNSET)
        app: AppResponseDto | Unset
        if isinstance(_app, Unset):
            app = UNSET
        else:
            app = AppResponseDto.from_dict(_app)

        channel_response_dto = cls(
            id=id,
            channel_id=channel_id,
            org_id=org_id,
            app_id=app_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            app=app,
        )

        channel_response_dto.additional_properties = d
        return channel_response_dto

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
