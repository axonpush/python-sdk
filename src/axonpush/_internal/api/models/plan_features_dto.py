from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PlanFeaturesDto")


@_attrs_define
class PlanFeaturesDto:
    """
    Attributes:
        rbac (bool | Unset):
        audit_log (bool | Unset):
        sso (bool | Unset):
        custom_retention (bool | Unset):
    """

    rbac: bool | Unset = UNSET
    audit_log: bool | Unset = UNSET
    sso: bool | Unset = UNSET
    custom_retention: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rbac = self.rbac

        audit_log = self.audit_log

        sso = self.sso

        custom_retention = self.custom_retention

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rbac is not UNSET:
            field_dict["rbac"] = rbac
        if audit_log is not UNSET:
            field_dict["auditLog"] = audit_log
        if sso is not UNSET:
            field_dict["sso"] = sso
        if custom_retention is not UNSET:
            field_dict["customRetention"] = custom_retention

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rbac = d.pop("rbac", UNSET)

        audit_log = d.pop("auditLog", UNSET)

        sso = d.pop("sso", UNSET)

        custom_retention = d.pop("customRetention", UNSET)

        plan_features_dto = cls(
            rbac=rbac,
            audit_log=audit_log,
            sso=sso,
            custom_retention=custom_retention,
        )

        plan_features_dto.additional_properties = d
        return plan_features_dto

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
