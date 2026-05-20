from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.channel_response_dto import ChannelResponseDto


T = TypeVar("T", bound="AppResponseDto")


@_attrs_define
class AppResponseDto:
    """
    Attributes:
        id (str):
        app_id (str):
        org_id (str):
        name (str):
        created_at (str):
        creator_user_id (str | Unset):
        updated_at (str | Unset):
        deleted_at (str | Unset):
        channels (list[ChannelResponseDto] | Unset):
    """

    id: str
    app_id: str
    org_id: str
    name: str
    created_at: str
    creator_user_id: str | Unset = UNSET
    updated_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    channels: list[ChannelResponseDto] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.channel_response_dto import ChannelResponseDto

        id = self.id

        app_id = self.app_id

        org_id = self.org_id

        name = self.name

        created_at = self.created_at

        creator_user_id = self.creator_user_id

        updated_at = self.updated_at

        deleted_at = self.deleted_at

        channels: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.channels, Unset):
            channels = []
            for channels_item_data in self.channels:
                channels_item = channels_item_data.to_dict()
                channels.append(channels_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "appId": app_id,
                "orgId": org_id,
                "name": name,
                "createdAt": created_at,
            }
        )
        if creator_user_id is not UNSET:
            field_dict["creatorUserId"] = creator_user_id
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if channels is not UNSET:
            field_dict["channels"] = channels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.channel_response_dto import ChannelResponseDto

        d = dict(src_dict)
        id = d.pop("id")

        app_id = d.pop("appId")

        org_id = d.pop("orgId")

        name = d.pop("name")

        created_at = d.pop("createdAt")

        creator_user_id = d.pop("creatorUserId", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        _channels = d.pop("channels", UNSET)
        channels: list[ChannelResponseDto] | Unset = UNSET
        if _channels is not UNSET:
            channels = []
            for channels_item_data in _channels:
                channels_item = ChannelResponseDto.from_dict(channels_item_data)

                channels.append(channels_item)

        app_response_dto = cls(
            id=id,
            app_id=app_id,
            org_id=org_id,
            name=name,
            created_at=created_at,
            creator_user_id=creator_user_id,
            updated_at=updated_at,
            deleted_at=deleted_at,
            channels=channels,
        )

        app_response_dto.additional_properties = d
        return app_response_dto

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
