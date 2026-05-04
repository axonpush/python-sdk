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


def derive_runnable_name(
    serialized: Optional[Dict[str, Any]],
    kwargs: Dict[str, Any],
) -> str:
    """Derive a human-readable name for a LangChain Runnable / chain start.

    LangChain's ``on_chain_start`` was originally designed for plain ``Chain``
    classes that populate ``serialized = {"name": "<ChainClass>", "id": [...]}``.
    LangGraph nodes — which compile down to anonymous Runnables — instead pass
    an empty ``serialized={}`` and put the node identity in ``kwargs["name"]``
    plus ``kwargs["metadata"]["langgraph_node"]``. Without this fallback every
    LangGraph step shows up as ``chain_type: "unknown"`` in the trace.

    Resolution order:
        1. ``kwargs["name"]`` (explicit Runnable name from LangChain)
        2. ``kwargs["metadata"]["langgraph_node"]`` (LangGraph node id)
        3. ``serialized["name"]`` (legacy Chain-style)
        4. last segment of ``serialized["id"]`` (qualified Runnable path)
        5. ``"Runnable"`` fallback (better than "unknown" — actually true)
    """
    name = kwargs.get("name")
    if name:
        return str(name)
    md = kwargs.get("metadata") or {}
    node = md.get("langgraph_node")
    if node:
        return str(node)
    s = serialized or {}
    if s.get("name"):
        return str(s["name"])
    sid = s.get("id")
    if isinstance(sid, list) and sid:
        return str(sid[-1])
    return "Runnable"


def derive_model_name(
    serialized: Optional[Dict[str, Any]],
    kwargs: Dict[str, Any],
) -> str:
    """Derive the actual configured LLM model id, not the wrapper class name.

    ``serialized["name"]`` returns the LangChain wrapper class (e.g.
    ``"ChatOpenAI"``), which is rarely what callers want to see in a trace.
    The real model id lives either in:
        - ``kwargs["invocation_params"]["model"|"model_name"]`` at call-time
          (set by every modern Chat* integration), or
        - ``serialized["kwargs"]["model"|"model_name"]`` at construction-time.

    Resolution order:
        1. invocation_params model / model_name / model_id
        2. serialized.kwargs model / model_name / model_id
        3. serialized.name (class-name fallback — still useful)
        4. ``"unknown"``
    """
    inv = kwargs.get("invocation_params") or {}
    for k in ("model", "model_name", "model_id"):
        v = inv.get(k)
        if v:
            return str(v)
    s = serialized or {}
    sk = s.get("kwargs") or {}
    for k in ("model", "model_name", "model_id"):
        v = sk.get(k)
        if v:
            return str(v)
    if s.get("name"):
        return str(s["name"])
    return "unknown"


def extract_run_metadata(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Pull useful per-run metadata out of LangChain callback ``**kwargs``.

    The ``metadata=`` and ``tags=`` arguments LangChain passes to every
    callback contain framework-level context (LangGraph node, thread id,
    user-supplied tags) that's invaluable when triaging a trace but is
    currently silently discarded by the SDK. This helper returns a small dict
    suitable for shallow-merging into the per-event ``metadata`` payload.

    Returned keys (each only when non-empty):
        - ``langgraph_node``: LangGraph node identifier (e.g. ``"researcher"``)
        - ``langgraph_step``: integer step counter within the graph
        - ``langgraph_triggers``: list of edges that triggered this node
        - ``run_type``: LangChain run type (``"chain" | "llm" | "tool" | ...``)
        - ``tags``: user-supplied tags list
    """
    out: Dict[str, Any] = {}
    md = kwargs.get("metadata") or {}
    for k in ("langgraph_node", "langgraph_step", "langgraph_triggers", "thread_id"):
        v = md.get(k)
        if v is not None and v != "":
            out[k] = v
    run_type = kwargs.get("run_type")
    if run_type:
        out["run_type"] = str(run_type)
    tags = kwargs.get("tags")
    if tags:
        out["tags"] = list(tags) if not isinstance(tags, list) else tags
    return out


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
