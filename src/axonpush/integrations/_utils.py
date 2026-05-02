"""Internal helpers shared across integrations."""

from __future__ import annotations

import asyncio
import json
import warnings
from typing import Any, Dict, Optional


def coerce_channel_id(value: int | str) -> str:
    """Normalize a user-supplied channel_id to the canonical ``str`` form.

    v0.0.10 froze ``channel_id`` as a ``str`` UUID on the public boundary.
    Integrations still accept ``int`` to soften the migration for v0.0.9
    callers that coded against ``channel_id: int``; an ``int`` value emits
    a ``DeprecationWarning`` once and is stringified for the wire.

    Args:
        value: The user-supplied channel id, either ``int`` or ``str``.

    Returns:
        A ``str`` channel id ready to pass to ``client.events.publish``.

    Raises:
        TypeError: If the value is neither ``int`` nor ``str``.
    """
    if isinstance(value, bool):
        raise TypeError(f"channel_id must be int | str, got bool: {value!r}")
    if isinstance(value, int):
        warnings.warn(
            "channel_id as int is deprecated; pass a string UUID instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return str(value)
    if isinstance(value, str):
        return value
    raise TypeError(f"channel_id must be int | str, got {type(value).__name__}")


def is_async_client(client: Any) -> bool:
    """Return ``True`` if ``client`` is an ``AsyncAxonPush`` or a duck-typed equivalent.

    The integration layer never imports the async client class at module
    top-level (Stream A churn risk), so we feature-detect by checking
    whether ``client.events.publish`` is a coroutine function. The real
    :class:`AsyncAxonPush` from Stream A is detected first via
    ``isinstance`` for symmetry with the sync path.
    """
    _AsyncAxonPush: Any
    try:
        from axonpush.client import AsyncAxonPush as _AsyncAxonPush  # noqa: F811
    except Exception:  # pragma: no cover - defensive
        _AsyncAxonPush = None
    if _AsyncAxonPush is not None and isinstance(client, _AsyncAxonPush):
        return True
    import inspect

    publish = getattr(getattr(client, "events", None), "publish", None)
    return inspect.iscoroutinefunction(publish)


def safe_serialize(obj: Any, max_len: int = 2000) -> Any:
    """JSON-roundtrip an object, falling back to a truncated repr."""
    try:
        s = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj)[:max_len]
    if len(s) <= max_len:
        return json.loads(s)
    return s[:max_len]


def fire_and_forget(result: Any) -> None:
    """If ``result`` is a coroutine, schedule it on the running loop, else no-op."""
    if asyncio.iscoroutine(result):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(result)
        except RuntimeError:
            pass


def build_resource(
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
    environment: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Assemble an OTel ``resource`` dict from the three common attributes."""
    resource: Dict[str, Any] = {}
    if service_name is not None:
        resource["service.name"] = service_name
    if service_version is not None:
        resource["service.version"] = service_version
    if environment is not None:
        resource["deployment.environment"] = environment
    return resource or None
