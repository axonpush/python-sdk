"""Trace propagation primitives for the AxonPush SDK.

A :class:`TraceContext` carries a UUID4 ``trace_id`` plus a monotonic span-id
generator. The current context is stored in a :class:`~contextvars.ContextVar`
so each asyncio task — and each thread that copies the parent's context —
sees its own value.

The transport layer reads the current context and injects
``X-Axonpush-Trace-Id`` on outgoing requests when one is set.
"""

from __future__ import annotations

import hashlib
import secrets
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

    def next_span_id(self) -> str:
        """Return a fresh W3C-compatible span identifier.

        Returns:
            A non-zero 16-character lowercase hexadecimal string.
        """
        return secrets.token_hex(8)

    def w3c_trace_id(self) -> str:
        """Return this context's identifier as a W3C 32-hex trace id."""
        compact = self.trace_id.replace("-", "").lower()
        if len(compact) == 32 and compact != "0" * 32:
            try:
                int(compact, 16)
            except ValueError:
                pass
            else:
                return compact
        return hashlib.sha256(self.trace_id.encode()).hexdigest()[:32]

    def traceparent(self, span_id: str | None = None) -> str:
        """Build a sampled W3C ``traceparent`` header."""
        resolved_span_id = span_id or self.next_span_id()
        return f"00-{self.w3c_trace_id()}-{resolved_span_id}-01"


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
