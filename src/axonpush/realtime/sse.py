from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional, Union

from axonpush._http import SyncTransport
from axonpush.models.events import Event, EventType


class SSESubscription:
    """High-level sync SSE consumer that yields parsed Event models.

    Usage::

        with client.channels.subscribe_sse(channel_id=1) as sub:
            for event in sub:
                print(event.agent_id, event.payload)
    """

    def __init__(
        self,
        transport: SyncTransport,
        channel_id: int,
        *,
        event_identifier: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        self._transport = transport
        params = _build_filter_params(agent_id, event_type, trace_id)

        if event_identifier:
            path = f"/channel/{channel_id}/{event_identifier}/subscribe"
        else:
            path = f"/channel/{channel_id}/subscribe"

        self._cm = transport.stream_sse(path, params=params)
        self._source: Any = None

    def __enter__(self) -> SSESubscription:
        self._source = self._cm.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        self._cm.__exit__(*args)

    def __iter__(self) -> Iterator[Event]:
        if self._source is None:
            raise RuntimeError("SSESubscription must be used as a context manager")
        for sse_event in self._source.iter_sse():
            if sse_event.event == "message" and sse_event.data:
                try:
                    data = json.loads(sse_event.data)
                    yield Event.model_validate(data)
                except (json.JSONDecodeError, Exception):
                    continue


class AsyncSSESubscription:
    """High-level async SSE consumer.

    Note: httpx-sse's async connect_sse requires a running httpx.AsyncClient
    stream. For full async SSE, use the WebSocket client instead, or
    consume the raw async transport. This is a placeholder for when
    httpx-sse adds full async EventSource support.
    """

    pass


def _build_filter_params(
    agent_id: Optional[str],
    event_type: Optional[Union[EventType, str]],
    trace_id: Optional[str],
) -> Dict[str, str]:
    params: Dict[str, str] = {}
    if agent_id is not None:
        params["agentId"] = agent_id
    if event_type is not None:
        params["eventType"] = str(
            event_type.value if isinstance(event_type, EventType) else event_type
        )
    if trace_id is not None:
        params["traceId"] = trace_id
    return params
