from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open
from axonpush._tracing import get_or_create_trace
from axonpush.models.events import CreateEventParams, Event, EventType
from axonpush.resources.events_query import EventQuery


def _build_query(
    channel_id: Optional[str] = None,
    *,
    app_id: Optional[str] = None,
    environment_id: Optional[str] = None,
    event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = None,
    agent_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    cursor: Optional[str] = None,
    limit: Optional[int] = None,
    payload_filter: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    query = EventQuery(
        channel_id=channel_id,
        app_id=app_id,
        environment_id=environment_id,
        event_type=event_type,
        agent_id=agent_id,
        trace_id=trace_id,
        since=since,
        until=until,
        cursor=cursor,
        limit=limit,
        payload_filter=payload_filter,
    )
    return query.to_query_params()


def _coerce_results(data: Any) -> List[Event]:
    items = data
    if isinstance(data, dict):
        items = data.get("data", [])
    if not isinstance(items, list):
        return []
    return [Event.model_validate(item) for item in items]


class EventsResource:
    """Synchronous resource for publishing, listing, and searching events."""

    def __init__(
        self,
        transport: SyncTransport,
        *,
        environment: Optional[str] = None,
    ) -> None:
        self._transport = transport
        self._environment = environment

    def publish(
        self,
        identifier: str,
        payload: Dict[str, Any],
        channel_id: Union[int, str],
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_event_id: Optional[int] = None,
        event_type: Optional[Union[EventType, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
    ) -> Optional[Event]:
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
            environment=environment or self._environment,
        )
        data = self._transport.request(
            "POST", "/event", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Event.model_validate(data)

    def list(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = None,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
        payload_filter: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
    ) -> List[Event]:
        params = _build_query(
            channel_id=str(channel_id),
            event_type=event_type,
            agent_id=agent_id,
            trace_id=trace_id,
            since=since,
            until=until,
            cursor=cursor,
            limit=limit,
            payload_filter=payload_filter,
        )
        effective_env = environment or self._environment
        if effective_env:
            params["environment"] = effective_env
        data = self._transport.request("GET", "/event", params=params)
        if _is_fail_open(data):
            return []
        return _coerce_results(data)

    def search(
        self,
        *,
        channel_id: Optional[Union[int, str]] = None,
        app_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = None,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
        payload_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Event]:
        params = _build_query(
            channel_id=str(channel_id) if channel_id is not None else None,
            app_id=app_id,
            environment_id=environment_id,
            event_type=event_type,
            agent_id=agent_id,
            trace_id=trace_id,
            since=since,
            until=until,
            cursor=cursor,
            limit=limit,
            payload_filter=payload_filter,
        )
        data = self._transport.request("GET", "/event/search", params=params)
        if _is_fail_open(data):
            return []
        return _coerce_results(data)


class AsyncEventsResource:
    """Asynchronous resource for publishing, listing, and searching events."""

    def __init__(
        self,
        transport: AsyncTransport,
        *,
        environment: Optional[str] = None,
    ) -> None:
        self._transport = transport
        self._environment = environment

    async def publish(
        self,
        identifier: str,
        payload: Dict[str, Any],
        channel_id: Union[int, str],
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_event_id: Optional[int] = None,
        event_type: Optional[Union[EventType, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
    ) -> Optional[Event]:
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
            environment=environment or self._environment,
        )
        data = await self._transport.request(
            "POST", "/event", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Event.model_validate(data)

    async def list(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = None,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
        payload_filter: Optional[Dict[str, Any]] = None,
        environment: Optional[str] = None,
    ) -> List[Event]:
        params = _build_query(
            channel_id=str(channel_id),
            event_type=event_type,
            agent_id=agent_id,
            trace_id=trace_id,
            since=since,
            until=until,
            cursor=cursor,
            limit=limit,
            payload_filter=payload_filter,
        )
        effective_env = environment or self._environment
        if effective_env:
            params["environment"] = effective_env
        data = await self._transport.request("GET", "/event", params=params)
        if _is_fail_open(data):
            return []
        return _coerce_results(data)

    async def search(
        self,
        *,
        channel_id: Optional[Union[int, str]] = None,
        app_id: Optional[str] = None,
        environment_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = None,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        cursor: Optional[str] = None,
        limit: int = 100,
        payload_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Event]:
        params = _build_query(
            channel_id=str(channel_id) if channel_id is not None else None,
            app_id=app_id,
            environment_id=environment_id,
            event_type=event_type,
            agent_id=agent_id,
            trace_id=trace_id,
            since=since,
            until=until,
            cursor=cursor,
            limit=limit,
            payload_filter=payload_filter,
        )
        data = await self._transport.request("GET", "/event/search", params=params)
        if _is_fail_open(data):
            return []
        return _coerce_results(data)
