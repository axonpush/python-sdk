from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from axonpush._http import AsyncTransport, SyncTransport
from axonpush._tracing import get_or_create_trace
from axonpush.models.events import CreateEventParams, Event, EventType


class EventsResource:
    """Synchronous resource for publishing and listing events."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def publish(
        self,
        identifier: str,
        payload: Dict[str, Any],
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_event_id: Optional[int] = None,
        event_type: Optional[Union[EventType, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Publish an event to a channel (POST /event)."""
        if trace_id is None:
            trace_id = get_or_create_trace().trace_id

        body = CreateEventParams(
            identifier=identifier,
            payload=payload,
            channel_id=channel_id,
            agent_id=agent_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_event_id=parent_event_id,
            event_type=EventType(event_type) if isinstance(event_type, str) else event_type,
            metadata=metadata,
        )
        data = self._transport.request(
            "POST", "/event", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        return Event.model_validate(data)

    def list(
        self, channel_id: int, *, page: int = 1, limit: int = 10
    ) -> List[Event]:
        """List events in a channel (GET /event/:channelId/list)."""
        data = self._transport.request(
            "GET",
            f"/event/{channel_id}/list",
            params={"page": page, "limit": limit},
        )
        items = data.get("data", data) if isinstance(data, dict) else data
        return [Event.model_validate(e) for e in items]


class AsyncEventsResource:
    """Asynchronous resource for publishing and listing events."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def publish(
        self,
        identifier: str,
        payload: Dict[str, Any],
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_event_id: Optional[int] = None,
        event_type: Optional[Union[EventType, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Publish an event to a channel (POST /event)."""
        if trace_id is None:
            trace_id = get_or_create_trace().trace_id

        body = CreateEventParams(
            identifier=identifier,
            payload=payload,
            channel_id=channel_id,
            agent_id=agent_id,
            trace_id=trace_id,
            span_id=span_id,
            parent_event_id=parent_event_id,
            event_type=EventType(event_type) if isinstance(event_type, str) else event_type,
            metadata=metadata,
        )
        data = await self._transport.request(
            "POST", "/event", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        return Event.model_validate(data)

    async def list(
        self, channel_id: int, *, page: int = 1, limit: int = 10
    ) -> List[Event]:
        """List events in a channel (GET /event/:channelId/list)."""
        data = await self._transport.request(
            "GET",
            f"/event/{channel_id}/list",
            params={"page": page, "limit": limit},
        )
        items = data.get("data", data) if isinstance(data, dict) else data
        return [Event.model_validate(e) for e in items]
