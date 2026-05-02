from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SsoConnectionResponseDto")


@_attrs_define
class SsoConnectionResponseDto:
    """
    Attributes:
        client_id (str):
        tenant (str | Unset):
        product (str | Unset):
        default_redirect_url (str | Unset):
        redirect_url (list[str] | Unset):
    """

    client_id: str
    tenant: str | Unset = UNSET
    product: str | Unset = UNSET
    default_redirect_url: str | Unset = UNSET
    redirect_url: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        client_id = self.client_id

        tenant = self.tenant

        product = self.product

        default_redirect_url = self.default_redirect_url

        redirect_url: list[str] | Unset = UNSET
        if not isinstance(self.redirect_url, Unset):
            redirect_url = self.redirect_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "clientID": client_id,
            }
        )
        if tenant is not UNSET:
            field_dict["tenant"] = tenant
        if product is not UNSET:
            field_dict["product"] = product
        if default_redirect_url is not UNSET:
            field_dict["defaultRedirectUrl"] = default_redirect_url
        if redirect_url is not UNSET:
            field_dict["redirectUrl"] = redirect_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client_id = d.pop("clientID")

        tenant = d.pop("tenant", UNSET)

        product = d.pop("product", UNSET)

        default_redirect_url = d.pop("defaultRedirectUrl", UNSET)

        redirect_url = cast(list[str], d.pop("redirectUrl", UNSET))

        sso_connection_response_dto = cls(
            client_id=client_id,
            tenant=tenant,
            product=product,
            default_redirect_url=default_redirect_url,
            redirect_url=redirect_url,
        )

        sso_connection_response_dto.additional_properties = d
        return sso_connection_response_dto

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
