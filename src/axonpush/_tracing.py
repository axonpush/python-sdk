"""Trace propagation primitives for the AxonPush SDK.

A :class:`TraceContext` carries a UUID4 ``trace_id`` plus a monotonic span-id
generator. The current context is stored in a :class:`~contextvars.ContextVar`
so each asyncio task — and each thread that copies the parent's context —
sees its own value.

The transport layer reads the current context and injects
``X-Axonpush-Trace-Id`` on outgoing requests when one is set.
"""

from __future__ import annotations

import threading
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, field

_current_trace: ContextVar["TraceContext | None"] = ContextVar("_current_trace", default=None)


@dataclass
class TraceContext:
    """A correlation context shared across SDK calls.

    Attributes:
        trace_id: A UUID4 string. Generated automatically when not supplied.
    """

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    _span_counter: int = field(default=0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def next_span_id(self) -> str:
        """Return a fresh, monotonically-increasing span identifier.

        Returns:
            A UUID4 string. Each call yields a distinct value; the internal
            counter is bumped under a lock so concurrent threads stay safe.
        """
        with self._lock:
            self._span_counter += 1
        return str(uuid.uuid4())


def get_or_create_trace(trace_id: str | None = None) -> TraceContext:
    """Return the current trace, creating one if necessary.

    Args:
        trace_id: When provided, install a new context with this id and
            return it (overwriting any existing context). When ``None``,
            return the current context, or create one if no context is
            active in the current task/thread.

    Returns:
        The active :class:`TraceContext`.
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
    """Return the active :class:`TraceContext`, or ``None`` if none is set."""
    return _current_trace.get()


def set_current_trace(ctx: TraceContext) -> Token[TraceContext | None]:
    """Install ``ctx`` as the current trace and return a reset token.

    Args:
        ctx: The context to make active in the current task/thread.

    Returns:
        A :class:`~contextvars.Token` suitable for passing back to
        :func:`_clear_current_trace` to restore the previous value.
    """
    return _current_trace.set(ctx)


def _clear_current_trace(token: Token[TraceContext | None]) -> None:
    """Reset the current trace to whatever was active before ``token``."""
    _current_trace.reset(token)


__all__ = [
    "TraceContext",
    "current_trace",
    "get_or_create_trace",
    "set_current_trace",
]
