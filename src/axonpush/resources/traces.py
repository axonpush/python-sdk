"""Traces resource — list, summarise, fetch events for a trace."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from axonpush._internal.api.api.traces import (
    trace_controller_get_dashboard_stats as _stats_op,
    trace_controller_get_trace_events as _events_op,
    trace_controller_get_trace_summary as _summary_op,
    trace_controller_list_traces as _list_op,
)
from axonpush._internal.api.types import UNSET
from axonpush.models import (
    EventDetails,
    TraceStats,
    TraceSummary,
)
from axonpush._internal.api.models import TraceControllerListTracesResponse200

if TYPE_CHECKING:
    from axonpush.resources._base import AsyncClientProtocol, SyncClientProtocol


def _opt(value: object) -> object:
    return value if value is not None else UNSET


class Traces:
    """Synchronous trace queries."""

    def __init__(self, client: SyncClientProtocol) -> None:
        self._client = client

    def list(
        self,
        *,
        page: float | None = None,
        limit: float | None = None,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceControllerListTracesResponse200 | None:
        """List traces with optional pagination + scope filters.

        Args:
            page: 1-indexed page number.
            limit: Page size.
            app_id: Restrict to a single app UUID.
            environment: Restrict to an environment slug.
        """
        return self._client._invoke(
            _list_op.sync,
            page=_opt(page),
            limit=_opt(limit),
            app_id=_opt(app_id),
            environment=_opt(environment),
        )

    def stats(
        self,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceStats | None:
        """Dashboard stats — totals, error rate, events-by-hour buckets."""
        return self._client._invoke(
            _stats_op.sync, app_id=_opt(app_id), environment=_opt(environment)
        )

    def events(
        self,
        trace_id: str,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> List[EventDetails] | None:
        """List the events that make up a trace, in order."""
        return self._client._invoke(
            _events_op.sync,
            trace_id=trace_id,
            app_id=_opt(app_id),
            environment=_opt(environment),
        )

    def summary(
        self,
        trace_id: str,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceSummary | None:
        """Get a single-trace summary (counts + duration)."""
        return self._client._invoke(
            _summary_op.sync,
            trace_id=trace_id,
            app_id=_opt(app_id),
            environment=_opt(environment),
        )


class AsyncTraces:
    """Async sibling of :class:`Traces`."""

    def __init__(self, client: AsyncClientProtocol) -> None:
        self._client = client

    async def list(
        self,
        *,
        page: float | None = None,
        limit: float | None = None,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceControllerListTracesResponse200 | None:
        """See :meth:`Traces.list`."""
        return await self._client._invoke(
            _list_op.asyncio,
            page=_opt(page),
            limit=_opt(limit),
            app_id=_opt(app_id),
            environment=_opt(environment),
        )

    async def stats(
        self,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceStats | None:
        """See :meth:`Traces.stats`."""
        return await self._client._invoke(
            _stats_op.asyncio, app_id=_opt(app_id), environment=_opt(environment)
        )

    async def events(
        self,
        trace_id: str,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> List[EventDetails] | None:
        """See :meth:`Traces.events`."""
        return await self._client._invoke(
            _events_op.asyncio,
            trace_id=trace_id,
            app_id=_opt(app_id),
            environment=_opt(environment),
        )

    async def summary(
        self,
        trace_id: str,
        *,
        app_id: str | None = None,
        environment: str | None = None,
    ) -> TraceSummary | None:
        """See :meth:`Traces.summary`."""
        return await self._client._invoke(
            _summary_op.asyncio,
            trace_id=trace_id,
            app_id=_opt(app_id),
            environment=_opt(environment),
        )
