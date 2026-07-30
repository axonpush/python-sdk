from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.admin_org_list_item_dto import AdminOrgListItemDto


T = TypeVar("T", bound="AdminOrgListDto")


@_attrs_define
class AdminOrgListDto:
    """
    Attributes:
        total (float): Number of orgs matching the query (before the response cap)
        truncated (bool): True when results were capped and not all matches are returned
        orgs (list[AdminOrgListItemDto]):
    """

    total: float
    truncated: bool
    orgs: list[AdminOrgListItemDto]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto

        total = self.total

        truncated = self.truncated

        orgs = []
        for orgs_item_data in self.orgs:
            orgs_item = orgs_item_data.to_dict()
            orgs.append(orgs_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "truncated": truncated,
                "orgs": orgs,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.admin_org_list_item_dto import AdminOrgListItemDto

        d = dict(src_dict)
        total = d.pop("total")

        truncated = d.pop("truncated")

        orgs = []
        _orgs = d.pop("orgs")
        for orgs_item_data in _orgs:
            orgs_item = AdminOrgListItemDto.from_dict(orgs_item_data)

            orgs.append(orgs_item)

        admin_org_list_dto = cls(
            total=total,
            truncated=truncated,
            orgs=orgs,
        )

        admin_org_list_dto.additional_properties = d
        return admin_org_list_dto

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
