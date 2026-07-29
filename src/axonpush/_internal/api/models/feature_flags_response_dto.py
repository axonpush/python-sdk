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
        environments (bool):
        sentry_ingest (bool):
        async_ingest (bool):
        mcp_server (bool):
    """

    environments: bool
    sentry_ingest: bool
    async_ingest: bool
    mcp_server: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        environments = self.environments

        sentry_ingest = self.sentry_ingest

        async_ingest = self.async_ingest

        mcp_server = self.mcp_server

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "environments": environments,
                "sentryIngest": sentry_ingest,
                "asyncIngest": async_ingest,
                "mcpServer": mcp_server,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        environments = d.pop("environments")

        sentry_ingest = d.pop("sentryIngest")

        async_ingest = d.pop("asyncIngest")

        mcp_server = d.pop("mcpServer")

        feature_flags_response_dto = cls(
            environments=environments,
            sentry_ingest=sentry_ingest,
            async_ingest=async_ingest,
            mcp_server=mcp_server,
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
