from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, BinaryIO, Generator, TextIO, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.event_response_dto_metadata import EventResponseDtoMetadata
    from ..models.event_response_dto_payload import EventResponseDtoPayload


T = TypeVar("T", bound="EventResponseDto")


@_attrs_define
class EventResponseDto:
    """
    Attributes:
        id (str):
        event_id (str):
        org_id (str):
        app_id (str):
        channel_id (str):
        event_type (str):
        created_at (str):
        environment_id (str | Unset):
        agent_id (str | Unset):
        trace_id (str | Unset):
        span_id (str | Unset):
        parent_span_id (str | Unset):
        parent_event_id (str | Unset):
        identifier (str | Unset):
        payload (EventResponseDtoPayload | Unset):
        metadata (EventResponseDtoMetadata | Unset):
        occurred_at (str | Unset):
        start_time_unix_nano (str | Unset):
        end_time_unix_nano (str | Unset):
        source (str | Unset):
        semantic_kind (str | Unset):
        operation_name (str | Unset):
        duration_ms (float | Unset):
        status (str | Unset):
        service_name (str | Unset):
        service_version (str | Unset):
        provider_name (str | Unset):
        request_model (str | Unset):
        response_model (str | Unset):
        tool_name (str | Unset):
        total_tokens (float | Unset):
        cost_usd (float | Unset):
        updated_at (str | Unset):
        ttl (float | Unset):
    """

    id: str
    event_id: str
    org_id: str
    app_id: str
    channel_id: str
    event_type: str
    created_at: str
    environment_id: str | Unset = UNSET
    agent_id: str | Unset = UNSET
    trace_id: str | Unset = UNSET
    span_id: str | Unset = UNSET
    parent_span_id: str | Unset = UNSET
    parent_event_id: str | Unset = UNSET
    identifier: str | Unset = UNSET
    payload: EventResponseDtoPayload | Unset = UNSET
    metadata: EventResponseDtoMetadata | Unset = UNSET
    occurred_at: str | Unset = UNSET
    start_time_unix_nano: str | Unset = UNSET
    end_time_unix_nano: str | Unset = UNSET
    source: str | Unset = UNSET
    semantic_kind: str | Unset = UNSET
    operation_name: str | Unset = UNSET
    duration_ms: float | Unset = UNSET
    status: str | Unset = UNSET
    service_name: str | Unset = UNSET
    service_version: str | Unset = UNSET
    provider_name: str | Unset = UNSET
    request_model: str | Unset = UNSET
    response_model: str | Unset = UNSET
    tool_name: str | Unset = UNSET
    total_tokens: float | Unset = UNSET
    cost_usd: float | Unset = UNSET
    updated_at: str | Unset = UNSET
    ttl: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.event_response_dto_metadata import EventResponseDtoMetadata
        from ..models.event_response_dto_payload import EventResponseDtoPayload

        id = self.id

        event_id = self.event_id

        org_id = self.org_id

        app_id = self.app_id

        channel_id = self.channel_id

        event_type = self.event_type

        created_at = self.created_at

        environment_id = self.environment_id

        agent_id = self.agent_id

        trace_id = self.trace_id

        span_id = self.span_id

        parent_span_id = self.parent_span_id

        parent_event_id = self.parent_event_id

        identifier = self.identifier

        payload: dict[str, Any] | Unset = UNSET
        if not isinstance(self.payload, Unset):
            payload = self.payload.to_dict()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        occurred_at = self.occurred_at

        start_time_unix_nano = self.start_time_unix_nano

        end_time_unix_nano = self.end_time_unix_nano

        source = self.source

        semantic_kind = self.semantic_kind

        operation_name = self.operation_name

        duration_ms = self.duration_ms

        status = self.status

        service_name = self.service_name

        service_version = self.service_version

        provider_name = self.provider_name

        request_model = self.request_model

        response_model = self.response_model

        tool_name = self.tool_name

        total_tokens = self.total_tokens

        cost_usd = self.cost_usd

        updated_at = self.updated_at

        ttl = self.ttl

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "eventId": event_id,
                "orgId": org_id,
                "appId": app_id,
                "channelId": channel_id,
                "eventType": event_type,
                "createdAt": created_at,
            }
        )
        if environment_id is not UNSET:
            field_dict["environmentId"] = environment_id
        if agent_id is not UNSET:
            field_dict["agentId"] = agent_id
        if trace_id is not UNSET:
            field_dict["traceId"] = trace_id
        if span_id is not UNSET:
            field_dict["spanId"] = span_id
        if parent_span_id is not UNSET:
            field_dict["parentSpanId"] = parent_span_id
        if parent_event_id is not UNSET:
            field_dict["parentEventId"] = parent_event_id
        if identifier is not UNSET:
            field_dict["identifier"] = identifier
        if payload is not UNSET:
            field_dict["payload"] = payload
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if occurred_at is not UNSET:
            field_dict["occurredAt"] = occurred_at
        if start_time_unix_nano is not UNSET:
            field_dict["startTimeUnixNano"] = start_time_unix_nano
        if end_time_unix_nano is not UNSET:
            field_dict["endTimeUnixNano"] = end_time_unix_nano
        if source is not UNSET:
            field_dict["source"] = source
        if semantic_kind is not UNSET:
            field_dict["semanticKind"] = semantic_kind
        if operation_name is not UNSET:
            field_dict["operationName"] = operation_name
        if duration_ms is not UNSET:
            field_dict["durationMs"] = duration_ms
        if status is not UNSET:
            field_dict["status"] = status
        if service_name is not UNSET:
            field_dict["serviceName"] = service_name
        if service_version is not UNSET:
            field_dict["serviceVersion"] = service_version
        if provider_name is not UNSET:
            field_dict["providerName"] = provider_name
        if request_model is not UNSET:
            field_dict["requestModel"] = request_model
        if response_model is not UNSET:
            field_dict["responseModel"] = response_model
        if tool_name is not UNSET:
            field_dict["toolName"] = tool_name
        if total_tokens is not UNSET:
            field_dict["totalTokens"] = total_tokens
        if cost_usd is not UNSET:
            field_dict["costUsd"] = cost_usd
        if updated_at is not UNSET:
            field_dict["updatedAt"] = updated_at
        if ttl is not UNSET:
            field_dict["ttl"] = ttl

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_response_dto_metadata import EventResponseDtoMetadata
        from ..models.event_response_dto_payload import EventResponseDtoPayload

        d = dict(src_dict)
        id = d.pop("id")

        event_id = d.pop("eventId")

        org_id = d.pop("orgId")

        app_id = d.pop("appId")

        channel_id = d.pop("channelId")

        event_type = d.pop("eventType")

        created_at = d.pop("createdAt")

        environment_id = d.pop("environmentId", UNSET)

        agent_id = d.pop("agentId", UNSET)

        trace_id = d.pop("traceId", UNSET)

        span_id = d.pop("spanId", UNSET)

        parent_span_id = d.pop("parentSpanId", UNSET)

        parent_event_id = d.pop("parentEventId", UNSET)

        identifier = d.pop("identifier", UNSET)

        _payload = d.pop("payload", UNSET)
        payload: EventResponseDtoPayload | Unset
        if isinstance(_payload, Unset):
            payload = UNSET
        else:
            payload = EventResponseDtoPayload.from_dict(_payload)

        _metadata = d.pop("metadata", UNSET)
        metadata: EventResponseDtoMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = EventResponseDtoMetadata.from_dict(_metadata)

        occurred_at = d.pop("occurredAt", UNSET)

        start_time_unix_nano = d.pop("startTimeUnixNano", UNSET)

        end_time_unix_nano = d.pop("endTimeUnixNano", UNSET)

        source = d.pop("source", UNSET)

        semantic_kind = d.pop("semanticKind", UNSET)

        operation_name = d.pop("operationName", UNSET)

        duration_ms = d.pop("durationMs", UNSET)

        status = d.pop("status", UNSET)

        service_name = d.pop("serviceName", UNSET)

        service_version = d.pop("serviceVersion", UNSET)

        provider_name = d.pop("providerName", UNSET)

        request_model = d.pop("requestModel", UNSET)

        response_model = d.pop("responseModel", UNSET)

        tool_name = d.pop("toolName", UNSET)

        total_tokens = d.pop("totalTokens", UNSET)

        cost_usd = d.pop("costUsd", UNSET)

        updated_at = d.pop("updatedAt", UNSET)

        ttl = d.pop("ttl", UNSET)

        event_response_dto = cls(
            id=id,
            event_id=event_id,
            org_id=org_id,
            app_id=app_id,
            channel_id=channel_id,
            event_type=event_type,
            created_at=created_at,
            environment_id=environment_id,
            agent_id=agent_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            parent_event_id=parent_event_id,
            identifier=identifier,
            payload=payload,
            metadata=metadata,
            occurred_at=occurred_at,
            start_time_unix_nano=start_time_unix_nano,
            end_time_unix_nano=end_time_unix_nano,
            source=source,
            semantic_kind=semantic_kind,
            operation_name=operation_name,
            duration_ms=duration_ms,
            status=status,
            service_name=service_name,
            service_version=service_version,
            provider_name=provider_name,
            request_model=request_model,
            response_model=response_model,
            tool_name=tool_name,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            updated_at=updated_at,
            ttl=ttl,
        )

        event_response_dto.additional_properties = d
        return event_response_dto

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
