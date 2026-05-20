from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FeatureFlagsResponseDto")


@_attrs_define
class FeatureFlagsResponseDto:
    """
    Attributes:
        billing (bool):
        environments (bool):
        sentry_ingest (bool):
        async_ingest (bool):
    """

    billing: bool
    environments: bool
    sentry_ingest: bool
    async_ingest: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        billing = self.billing

        environments = self.environments

        sentry_ingest = self.sentry_ingest

        async_ingest = self.async_ingest

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "billing": billing,
                "environments": environments,
                "sentryIngest": sentry_ingest,
                "asyncIngest": async_ingest,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        billing = d.pop("billing")

        environments = d.pop("environments")

        sentry_ingest = d.pop("sentryIngest")

        async_ingest = d.pop("asyncIngest")

        feature_flags_response_dto = cls(
            billing=billing,
            environments=environments,
            sentry_ingest=sentry_ingest,
            async_ingest=async_ingest,
        )

        feature_flags_response_dto.additional_properties = d
        return feature_flags_response_dto

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
