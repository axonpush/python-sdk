from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AdminOrgMutationResponseDto")


@_attrs_define
class AdminOrgMutationResponseDto:
    """
    Attributes:
        ok (bool):  Example: True.
        subscription_status (None | str):
        plan (None | str):
    """

    ok: bool
    subscription_status: None | str
    plan: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ok = self.ok

        subscription_status: None | str
        subscription_status = self.subscription_status

        plan: None | str
        plan = self.plan

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ok": ok,
                "subscriptionStatus": subscription_status,
                "plan": plan,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ok = d.pop("ok")

        def _parse_subscription_status(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        subscription_status = _parse_subscription_status(d.pop("subscriptionStatus"))

        def _parse_plan(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        plan = _parse_plan(d.pop("plan"))

        admin_org_mutation_response_dto = cls(
            ok=ok,
            subscription_status=subscription_status,
            plan=plan,
        )

        admin_org_mutation_response_dto.additional_properties = d
        return admin_org_mutation_response_dto

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
