"""Events resource — publish, list, search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axonpush._internal.api.api.event import (
    event_controller_create_event as _create_op,
    event_controller_list_events as _list_op,
)
from axonpush._internal.api.api.events import (
    events_search_controller_search as _search_op,
)
from axonpush._internal.api.models import (
    CreateEventDto,
    CreateEventDtoEventType,
    CreateEventDtoMetadata,
    CreateEventDtoPayload,
)
from axonpush._internal.api.types import UNSET, Unset
from axonpush._tracing import get_or_create_trace
from axonpush.models import Event, EventListResponseDto, EventType

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _coerce_event_type(
    value: EventType | str | None,
) -> CreateEventDtoEventType | Unset:
    if value is None:
        return UNSET
    if isinstance(value, CreateEventDtoEventType):
        return value
    return CreateEventDtoEventType(value)


def _build_create_dto(
    *,
    identifier: str,
    payload: dict[str, Any],
    channel_id: str,
    agent_id: str | None,
    trace_id: str | None,
    span_id: str | None,
    parent_event_id: str | None,
    event_type: EventType | str | None,
    metadata: dict[str, Any] | None,
    environment: str | None,
) -> CreateEventDto:
    """Assemble the generated DTO with ``UNSET`` for omitted optionals."""
    resolved_trace = trace_id if trace_id is not None else get_or_create_trace().trace_id

    payload_dto = CreateEventDtoPayload()
    payload_dto.additional_properties = dict(payload)

    metadata_dto: CreateEventDtoMetadata | Unset = UNSET
    if metadata is not None:
        md = CreateEventDtoMetadata()
        md.additional_properties = dict(metadata)
        metadata_dto = md

    return CreateEventDto(
        identifier=identifier,
        payload=payload_dto,
        channel_id=channel_id,
        agent_id=agent_id if agent_id is not None else UNSET,
        trace_id=resolved_trace,
        span_id=span_id if span_id is not None else UNSET,
        parent_event_id=parent_event_id if parent_event_id is not None else UNSET,
        event_type=_coerce_event_type(event_type),
        metadata=metadata_dto,
        environment=environment if environment is not None else UNSET,
    )


class Events:
    """Publish, list, and search events."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def publish(
        self,
        identifier: str,
        payload: dict[str, Any],
        channel_id: str,
        *,
        agent_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_event_id: str | None = None,
        event_type: EventType | str | None = None,
        metadata: dict[str, Any] | None = None,
        environment: str | None = None,
    ) -> Event | None:
        """Publish a single event to a channel.

        Args:
            identifier: Stable event identifier (de-dup key on the backend).
            payload: Event body.
            channel_id: UUID of the target channel.
            agent_id: Optional agent that emitted the event.
            trace_id: Optional trace UUID; one is auto-created when omitted.
            span_id: Optional span UUID for span linking.
            parent_event_id: Optional parent event UUID.
            event_type: Enum or string. Defaults to ``custom`` server-side.
            metadata: Free-form metadata map.
            environment: Per-call override of the client-level environment.

        Returns:
            The persisted :class:`Event`, or ``None`` if ``fail_open`` swallowed
            a transport error.

        Raises:
            AxonPushError: When ``fail_open`` is False and the call fails.
        """
        body = _build_create_dto(
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
        )
        return self._client._invoke(_create_op.sync, body=body)

    def list(self, channel_id: str) -> EventListResponseDto | None:
        """List events for a channel (newest first).

        Args:
            channel_id: UUID of the channel.

        Returns:
            An :class:`EventListResponseDto` (``data`` + ``meta``) or ``None``
            on a fail-open swallow.
        """
        return self._client._invoke(_list_op.sync, channel_id=channel_id)

    def search(self) -> EventListResponseDto | None:
        """Search events across channels via ``GET /events/search``.

        Returns:
            An :class:`EventListResponseDto` or ``None`` on fail-open.
        """
        return self._client._invoke(_search_op.sync)


class AsyncEvents:
    """Async sibling of :class:`Events`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def publish(
        self,
        identifier: str,
        payload: dict[str, Any],
        channel_id: str,
        *,
        agent_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_event_id: str | None = None,
        event_type: EventType | str | None = None,
        metadata: dict[str, Any] | None = None,
        environment: str | None = None,
    ) -> Event | None:
        """Publish a single event to a channel. See :meth:`Events.publish`."""
        body = _build_create_dto(
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
        )
        return await self._client._invoke(_create_op.asyncio, body=body)

    async def list(self, channel_id: str) -> EventListResponseDto | None:
        """List events for a channel. See :meth:`Events.list`."""
        return await self._client._invoke(_list_op.asyncio, channel_id=channel_id)

    async def search(self) -> EventListResponseDto | None:
        """Search events. See :meth:`Events.search`."""
        return await self._client._invoke(_search_op.asyncio)
