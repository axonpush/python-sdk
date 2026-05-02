from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.setup_org_dto_action import SetupOrgDtoAction
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_organization_dto import CreateOrganizationDto


T = TypeVar("T", bound="SetupOrgDto")


@_attrs_define
class SetupOrgDto:
    """
    Attributes:
        action (SetupOrgDtoAction):
        org_create_props (CreateOrganizationDto | Unset):
        invitation_code (str | Unset):
    """

    action: SetupOrgDtoAction
    org_create_props: CreateOrganizationDto | Unset = UNSET
    invitation_code: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        action = self.action.value

        org_create_props: dict[str, Any] | Unset = UNSET
        if not isinstance(self.org_create_props, Unset):
            org_create_props = self.org_create_props.to_dict()

        invitation_code = self.invitation_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
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
        from ..models.create_organization_dto import CreateOrganizationDto

        d = dict(src_dict)
        action = SetupOrgDtoAction(d.pop("action"))

        _org_create_props = d.pop("orgCreateProps", UNSET)
        org_create_props: CreateOrganizationDto | Unset
        if isinstance(_org_create_props, Unset):
            org_create_props = UNSET
        else:
            org_create_props = CreateOrganizationDto.from_dict(_org_create_props)

        invitation_code = d.pop("invitationCode", UNSET)

        setup_org_dto = cls(
            action=action,
            org_create_props=org_create_props,
            invitation_code=invitation_code,
        )

        setup_org_dto.additional_properties = d
        return setup_org_dto

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
