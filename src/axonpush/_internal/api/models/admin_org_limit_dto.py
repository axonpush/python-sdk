from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminOrgLimitDto")


@_attrs_define
class AdminOrgLimitDto:
    """
    Attributes:
        plan_default (float | None): Plan-derived default (null = unlimited)
        override (float | None): Raw durable override: a number, -1 for unlimited, or null when unset
        effective (float | None): Effective value in force (null = unlimited)
    """

    plan_default: float | None
    override: float | None
    effective: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan_default: float | None
        plan_default = self.plan_default

        override: float | None
        override = self.override

        effective: float | None
        effective = self.effective

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "planDefault": plan_default,
                "override": override,
                "effective": effective,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_plan_default(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        plan_default = _parse_plan_default(d.pop("planDefault"))

        def _parse_override(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        override = _parse_override(d.pop("override"))

        def _parse_effective(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        effective = _parse_effective(d.pop("effective"))

        admin_org_limit_dto = cls(
            plan_default=plan_default,
            override=override,
            effective=effective,
        )

        admin_org_limit_dto.additional_properties = d
        return admin_org_limit_dto

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
