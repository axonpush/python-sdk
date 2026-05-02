"""Protocols used by every resource module.

Resources never touch transport directly. They go through the facade's
``_invoke`` chokepoint, which Stream A owns and which is responsible for
auth, retries, fail-open, and request-id propagation.
"""

from __future__ import annotations

from typing import Any, Protocol


class SyncClientProtocol(Protocol):
    """Subset of :class:`~axonpush.client.AxonPush` that resources rely on."""

    def _invoke(self, op: Any, /, **kwargs: Any) -> Any:
        """Run a generated sync op through the retry + fail-open chokepoint.

        ``op`` is a generated operation module (the file under
        ``axonpush._internal.api.api.<tag>.<op_name>``) that exposes
        ``sync_detailed``. The transport layer drives ``sync_detailed`` and
        returns the parsed response model.
        """
        ...


class AsyncClientProtocol(Protocol):
    """Subset of :class:`~axonpush.client.AsyncAxonPush` that resources rely on."""

    async def _invoke(self, op: Any, /, **kwargs: Any) -> Any:
        """Run a generated async op through the retry + fail-open chokepoint."""
        ...
