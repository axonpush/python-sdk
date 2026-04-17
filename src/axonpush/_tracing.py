from __future__ import annotations

import threading
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field

_current_trace: ContextVar[TraceContext | None] = ContextVar("_current_trace", default=None)


@dataclass
class TraceContext:
    """Holds a trace_id and generates sequential span IDs.

    Thread-safe via a lock on the span counter.
    Task-safe via contextvars (each asyncio Task inherits its own copy).
    """

    trace_id: str = field(default_factory=lambda: f"tr_{uuid.uuid4().hex[:16]}")
    _span_counter: int = field(default=0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def next_span_id(self) -> str:
        with self._lock:
            self._span_counter += 1
            counter = self._span_counter
        return f"sp_{self.trace_id[3:]}_{counter:04d}"


def get_or_create_trace(trace_id: str | None = None) -> TraceContext:
    """Get the current trace from context, or create a new one.

    If *trace_id* is provided, always creates a fresh context with that ID.
    If *trace_id* is None and a context already exists, returns it.
    Otherwise creates a new context with an auto-generated ID.
    """
    if trace_id is not None:
        ctx = TraceContext(trace_id=trace_id)
        _current_trace.set(ctx)
        return ctx

    existing = _current_trace.get()
    if existing is not None:
        return existing

    ctx = TraceContext()
    _current_trace.set(ctx)
    return ctx


def current_trace() -> TraceContext | None:
    """Return the current trace context, or None if not set."""
    return _current_trace.get()
