from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReleaseArtifactResponseDto")


@_attrs_define
class ReleaseArtifactResponseDto:
    """
    Attributes:
        org_id (str):
        version (str):
        artifact_id (str):
        name (str):
        size_bytes (float):
        storage_path (str):
        created_at (str):
        content_type (str | Unset):
        sha256 (str | Unset):
    """

    org_id: str
    version: str
    artifact_id: str
    name: str
    size_bytes: float
    storage_path: str
    created_at: str
    content_type: str | Unset = UNSET
    sha256: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        org_id = self.org_id

        version = self.version

        artifact_id = self.artifact_id

        name = self.name

        size_bytes = self.size_bytes

        storage_path = self.storage_path

        created_at = self.created_at

        content_type = self.content_type

        sha256 = self.sha256

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orgId": org_id,
                "version": version,
                "artifactId": artifact_id,
                "name": name,
                "sizeBytes": size_bytes,
                "storagePath": storage_path,
                "createdAt": created_at,
            }
        )
        if content_type is not UNSET:
            field_dict["contentType"] = content_type
        if sha256 is not UNSET:
            field_dict["sha256"] = sha256

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        org_id = d.pop("orgId")

        version = d.pop("version")

        artifact_id = d.pop("artifactId")

        name = d.pop("name")

        size_bytes = d.pop("sizeBytes")

        storage_path = d.pop("storagePath")

        created_at = d.pop("createdAt")

        content_type = d.pop("contentType", UNSET)

        sha256 = d.pop("sha256", UNSET)

        release_artifact_response_dto = cls(
            org_id=org_id,
            version=version,
            artifact_id=artifact_id,
            name=name,
            size_bytes=size_bytes,
            storage_path=storage_path,
            created_at=created_at,
            content_type=content_type,
            sha256=sha256,
        )

        release_artifact_response_dto.additional_properties = d
        return release_artifact_response_dto

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
