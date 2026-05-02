from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_invitation_dto_desired_role import CreateInvitationDtoDesiredRole
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateInvitationDto")


@_attrs_define
class CreateInvitationDto:
    """
    Attributes:
        invited_email (str):
        desired_role (CreateInvitationDtoDesiredRole):
    """

    invited_email: str
    desired_role: CreateInvitationDtoDesiredRole
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        invited_email = self.invited_email

        desired_role = self.desired_role.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "invitedEmail": invited_email,
                "desired_role": desired_role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        invited_email = d.pop("invitedEmail")

        desired_role = CreateInvitationDtoDesiredRole(d.pop("desired_role"))

        create_invitation_dto = cls(
            invited_email=invited_email,
            desired_role=desired_role,
        )

        create_invitation_dto.additional_properties = d
        return create_invitation_dto

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
