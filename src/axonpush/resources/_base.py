"""Protocols used by every resource module.

Resources never touch transport directly. They go through the facade's
``_invoke`` chokepoint, which Stream A owns and which is responsible for
auth, retries, fail-open, and request-id propagation.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Protocol, TypeVar


_R = TypeVar("_R")


class SyncClientProtocol(Protocol):
    """Subset of :class:`~axonpush.client.AxonPush` that resources rely on."""

    def _invoke(self, op: Callable[..., _R | None], /, **kwargs: Any) -> _R | None:
        """Run a generated sync op through the retry + fail-open chokepoint."""
        ...


class AsyncClientProtocol(Protocol):
    """Subset of :class:`~axonpush.client.AsyncAxonPush` that resources rely on."""

    async def _invoke(self, op: Callable[..., Awaitable[_R | None]], /, **kwargs: Any) -> _R | None:
        """Run a generated async op through the retry + fail-open chokepoint."""
        ...
