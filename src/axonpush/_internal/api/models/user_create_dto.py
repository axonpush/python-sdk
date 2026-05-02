from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_create_dto_action import UserCreateDtoAction
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.function import Function


T = TypeVar("T", bound="UserCreateDto")


@_attrs_define
class UserCreateDto:
    """
    Attributes:
        email (str):
        username (str):
        first_name (str):
        last_name (str):
        password (str):
        action (UserCreateDtoAction):
        org_create_props (Function | Unset):
        invitation_code (str | Unset):
    """

    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    action: UserCreateDtoAction
    org_create_props: Function | Unset = UNSET
    invitation_code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        email = self.email

        username = self.username

        first_name = self.first_name

        last_name = self.last_name

        password = self.password

        action = self.action.value

        org_create_props: dict[str, Any] | Unset = UNSET
        if not isinstance(self.org_create_props, Unset):
            org_create_props = self.org_create_props.to_dict()

        invitation_code = self.invitation_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "action": action,
            }
        )
        if org_create_props is not UNSET:
            field_dict["orgCreateProps"] = org_create_props
        if invitation_code is not UNSET:
            field_dict["invitationCode"] = invitation_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.function import Function

        d = dict(src_dict)
        email = d.pop("email")

        username = d.pop("username")

        first_name = d.pop("first_name")

        last_name = d.pop("last_name")

        password = d.pop("password")

        action = UserCreateDtoAction(d.pop("action"))

        _org_create_props = d.pop("orgCreateProps", UNSET)
        org_create_props: Function | Unset
        if isinstance(_org_create_props, Unset):
            org_create_props = UNSET
        else:
            org_create_props = Function.from_dict(_org_create_props)

        invitation_code = d.pop("invitationCode", UNSET)

        user_create_dto = cls(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            action=action,
            org_create_props=org_create_props,
            invitation_code=invitation_code,
        )

        user_create_dto.additional_properties = d
        return user_create_dto

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
