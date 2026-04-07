from __future__ import annotations

from typing import Any, Dict, Optional, Union

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open
from axonpush.models.channels import Channel, CreateChannelParams
from axonpush.models.events import EventType


class ChannelsResource:
    """Synchronous resource for channel CRUD and SSE subscriptions."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def create(self, name: str, app_id: int) -> Optional[Channel]:
        """Create a new channel (POST /channel)."""
        body = CreateChannelParams(name=name, app_id=app_id)
        data = self._transport.request(
            "POST", "/channel", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def get(self, channel_id: int) -> Optional[Channel]:
        """Get a channel by ID (GET /channel/:id)."""
        data = self._transport.request("GET", f"/channel/{channel_id}")
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def update(self, channel_id: int, **fields: Any) -> Optional[Channel]:
        """Update a channel (PUT /channel/:id)."""
        data = self._transport.request("PUT", f"/channel/{channel_id}", json=fields)
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def delete(self, channel_id: int) -> None:
        """Delete a channel (DELETE /channel/:id)."""
        self._transport.request("DELETE", f"/channel/{channel_id}")

    def subscribe_sse(
        self,
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,
    ) -> Any:
        """Subscribe to channel events via SSE (GET /channel/:channelId/subscribe).

        Returns a context manager yielding an httpx_sse.EventSource.
        Use ``realtime.sse.SSESubscription`` for a higher-level iterator.
        """
        params = _build_filter_params(agent_id, event_type, trace_id)
        return self._transport.stream_sse(f"/channel/{channel_id}/subscribe", params=params)

    def subscribe_event_sse(
        self,
        channel_id: int,
        event_identifier: str,
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,
    ) -> Any:
        """Subscribe to events by identifier via SSE."""
        params = _build_filter_params(agent_id, event_type, trace_id)
        return self._transport.stream_sse(
            f"/channel/{channel_id}/{event_identifier}/subscribe", params=params
        )


class AsyncChannelsResource:
    """Asynchronous resource for channel CRUD."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def create(self, name: str, app_id: int) -> Optional[Channel]:
        body = CreateChannelParams(name=name, app_id=app_id)
        data = await self._transport.request(
            "POST", "/channel", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def get(self, channel_id: int) -> Optional[Channel]:
        data = await self._transport.request("GET", f"/channel/{channel_id}")
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def update(self, channel_id: int, **fields: Any) -> Optional[Channel]:
        data = await self._transport.request("PUT", f"/channel/{channel_id}", json=fields)
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def delete(self, channel_id: int) -> None:
        await self._transport.request("DELETE", f"/channel/{channel_id}")


def _build_filter_params(
    agent_id: Optional[str],
    event_type: Optional[Union[EventType, str]],
    trace_id: Optional[str],
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if agent_id is not None:
        params["agentId"] = agent_id
    if event_type is not None:
        params["eventType"] = str(event_type.value if isinstance(event_type, EventType) else event_type)
    if trace_id is not None:
        params["traceId"] = trace_id
    return params
