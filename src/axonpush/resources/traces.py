from __future__ import annotations

from typing import List

from axonpush._http import AsyncTransport, SyncTransport
from axonpush.models.events import Event
from axonpush.models.traces import TraceListItem, TraceSummary


class TracesResource:
    """Synchronous resource for trace querying."""

    def __init__(self, transport: SyncTransport) -> None:
        self._transport = transport

    def list(self, *, page: int = 1, limit: int = 20) -> List[TraceListItem]:
        """List traces (GET /traces)."""
        data = self._transport.request(
            "GET", "/traces", params={"page": page, "limit": limit}
        )
        return [TraceListItem.model_validate(t) for t in data]

    def get_events(self, trace_id: str) -> List[Event]:
        """Get all events for a trace (GET /traces/:traceId/events)."""
        data = self._transport.request("GET", f"/traces/{trace_id}/events")
        return [Event.model_validate(e) for e in data]

    def get_summary(self, trace_id: str) -> TraceSummary:
        """Get trace summary (GET /traces/:traceId/summary)."""
        data = self._transport.request("GET", f"/traces/{trace_id}/summary")
        return TraceSummary.model_validate(data)


class AsyncTracesResource:
    """Asynchronous resource for trace querying."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def list(self, *, page: int = 1, limit: int = 20) -> List[TraceListItem]:
        data = await self._transport.request(
            "GET", "/traces", params={"page": page, "limit": limit}
        )
        return [TraceListItem.model_validate(t) for t in data]

    async def get_events(self, trace_id: str) -> List[Event]:
        data = await self._transport.request("GET", f"/traces/{trace_id}/events")
        return [Event.model_validate(e) for e in data]

    async def get_summary(self, trace_id: str) -> TraceSummary:
        data = await self._transport.request("GET", f"/traces/{trace_id}/summary")
        return TraceSummary.model_validate(data)
