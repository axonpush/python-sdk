from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_event_dto_event_type import CreateEventDtoEventType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_event_dto_metadata import CreateEventDtoMetadata
    from ..models.create_event_dto_payload import CreateEventDtoPayload


T = TypeVar("T", bound="CreateEventDto")


@_attrs_define
class CreateEventDto:
    """
    Attributes:
        identifier (str):
        payload (CreateEventDtoPayload):
        channel_id (str):
        agent_id (str | Unset):
        trace_id (str | Unset):
        span_id (str | Unset):
        parent_event_id (str | Unset):
        event_type (CreateEventDtoEventType | Unset):  Default: CreateEventDtoEventType.CUSTOM.
        metadata (CreateEventDtoMetadata | Unset):
        environment (str | Unset): Environment slug override. Only honored when the API key has
            allowEnvironmentOverride=true.
        sync (bool | Unset): When true, wait for the event to be persisted to the DB before returning. Use only for
            audit-critical calls — the default async path returns in under a millisecond. Default: False.
    """

    identifier: str
    payload: CreateEventDtoPayload
    channel_id: str
    agent_id: str | Unset = UNSET
    trace_id: str | Unset = UNSET
    span_id: str | Unset = UNSET
    parent_event_id: str | Unset = UNSET
    event_type: CreateEventDtoEventType | Unset = CreateEventDtoEventType.CUSTOM
    metadata: CreateEventDtoMetadata | Unset = UNSET
    environment: str | Unset = UNSET
    sync: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        identifier = self.identifier

        payload = self.payload.to_dict()

        channel_id = self.channel_id

        agent_id = self.agent_id

        trace_id = self.trace_id

        span_id = self.span_id

        parent_event_id = self.parent_event_id

        event_type: str | Unset = UNSET
        if not isinstance(self.event_type, Unset):
            event_type = self.event_type.value

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        environment = self.environment

        sync = self.sync

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identifier": identifier,
                "payload": payload,
                "channel_id": channel_id,
            }
        )
        if agent_id is not UNSET:
            field_dict["agentId"] = agent_id
        if trace_id is not UNSET:
            field_dict["traceId"] = trace_id
        if span_id is not UNSET:
            field_dict["spanId"] = span_id
        if parent_event_id is not UNSET:
            field_dict["parentEventId"] = parent_event_id
        if event_type is not UNSET:
            field_dict["eventType"] = event_type
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if environment is not UNSET:
            field_dict["environment"] = environment
        if sync is not UNSET:
            field_dict["sync"] = sync

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_event_dto_metadata import CreateEventDtoMetadata
        from ..models.create_event_dto_payload import CreateEventDtoPayload

        d = dict(src_dict)
        identifier = d.pop("identifier")

        payload = CreateEventDtoPayload.from_dict(d.pop("payload"))

        channel_id = d.pop("channel_id")

        agent_id = d.pop("agentId", UNSET)

        trace_id = d.pop("traceId", UNSET)

        span_id = d.pop("spanId", UNSET)

        parent_event_id = d.pop("parentEventId", UNSET)

        _event_type = d.pop("eventType", UNSET)
        event_type: CreateEventDtoEventType | Unset
        if isinstance(_event_type, Unset):
            event_type = UNSET
        else:
            event_type = CreateEventDtoEventType(_event_type)

        _metadata = d.pop("metadata", UNSET)
        metadata: CreateEventDtoMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreateEventDtoMetadata.from_dict(_metadata)

        environment = d.pop("environment", UNSET)

        sync = d.pop("sync", UNSET)

        create_event_dto = cls(
            identifier=identifier,
            payload=payload,
            channel_id=channel_id,
            agent_id=agent_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_event_id=parent_event_id,
            event_type=event_type,
            metadata=metadata,
            environment=environment,
            sync=sync,
        )

        create_event_dto.additional_properties = d
        return create_event_dto

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
