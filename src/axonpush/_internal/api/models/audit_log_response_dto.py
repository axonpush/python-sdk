from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.audit_log_actor_dto import AuditLogActorDto
    from ..models.audit_log_response_dto_metadata_type_0 import AuditLogResponseDtoMetadataType0


T = TypeVar("T", bound="AuditLogResponseDto")


@_attrs_define
class AuditLogResponseDto:
    """
    Attributes:
        id (str):
        audit_id (str):
        action (str):
        resource_type (str):
        created_at (str):
        organization_id (str | Unset):
        org_id (str | Unset):
        actor_id (None | str | Unset):
        resource_id (str | Unset):
        metadata (AuditLogResponseDtoMetadataType0 | None | Unset):
        ip_address (None | str | Unset):
        actor (AuditLogActorDto | None | Unset):
    """

    id: str
    audit_id: str
    action: str
    resource_type: str
    created_at: str
    organization_id: str | Unset = UNSET
    org_id: str | Unset = UNSET
    actor_id: None | str | Unset = UNSET
    resource_id: str | Unset = UNSET
    metadata: AuditLogResponseDtoMetadataType0 | None | Unset = UNSET
    ip_address: None | str | Unset = UNSET
    actor: AuditLogActorDto | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.audit_log_actor_dto import AuditLogActorDto
        from ..models.audit_log_response_dto_metadata_type_0 import AuditLogResponseDtoMetadataType0

        id = self.id

        audit_id = self.audit_id

        action = self.action

        resource_type = self.resource_type

        created_at = self.created_at

        organization_id = self.organization_id

        org_id = self.org_id

        actor_id: None | str | Unset
        if isinstance(self.actor_id, Unset):
            actor_id = UNSET
        else:
            actor_id = self.actor_id

        resource_id = self.resource_id

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, AuditLogResponseDtoMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        ip_address: None | str | Unset
        if isinstance(self.ip_address, Unset):
            ip_address = UNSET
        else:
            ip_address = self.ip_address

        actor: dict[str, Any] | None | Unset
        if isinstance(self.actor, Unset):
            actor = UNSET
        elif isinstance(self.actor, AuditLogActorDto):
            actor = self.actor.to_dict()
        else:
            actor = self.actor

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "auditId": audit_id,
                "action": action,
                "resourceType": resource_type,
                "createdAt": created_at,
            }
        )
        if organization_id is not UNSET:
            field_dict["organizationId"] = organization_id
        if org_id is not UNSET:
            field_dict["orgId"] = org_id
        if actor_id is not UNSET:
            field_dict["actorId"] = actor_id
        if resource_id is not UNSET:
            field_dict["resourceId"] = resource_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if ip_address is not UNSET:
            field_dict["ipAddress"] = ip_address
        if actor is not UNSET:
            field_dict["actor"] = actor

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_actor_dto import AuditLogActorDto
        from ..models.audit_log_response_dto_metadata_type_0 import AuditLogResponseDtoMetadataType0

        d = dict(src_dict)
        id = d.pop("id")

        audit_id = d.pop("auditId")

        action = d.pop("action")

        resource_type = d.pop("resourceType")

        created_at = d.pop("createdAt")

        organization_id = d.pop("organizationId", UNSET)

        org_id = d.pop("orgId", UNSET)

        def _parse_actor_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        actor_id = _parse_actor_id(d.pop("actorId", UNSET))

        resource_id = d.pop("resourceId", UNSET)

        def _parse_metadata(data: object) -> AuditLogResponseDtoMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = AuditLogResponseDtoMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogResponseDtoMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_ip_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip_address = _parse_ip_address(d.pop("ipAddress", UNSET))

        def _parse_actor(data: object) -> AuditLogActorDto | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                actor_type_1 = AuditLogActorDto.from_dict(data)

                return actor_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogActorDto | None | Unset, data)

        actor = _parse_actor(d.pop("actor", UNSET))

        audit_log_response_dto = cls(
            id=id,
            audit_id=audit_id,
            action=action,
            resource_type=resource_type,
            created_at=created_at,
            organization_id=organization_id,
            org_id=org_id,
            actor_id=actor_id,
            resource_id=resource_id,
            metadata=metadata,
            ip_address=ip_address,
            actor=actor,
        )

        audit_log_response_dto.additional_properties = d
        return audit_log_response_dto

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
