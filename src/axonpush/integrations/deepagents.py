"""DeepAgents integration for AxonPush.

DeepAgents builds on top of LangGraph + LangChain. The library exposes
the same callback hook surface as LangChain (``BaseCallbackHandler`` /
``AsyncCallbackHandler``), with extra tool naming conventions
(``write_todos`` for planning, ``task`` for sub-agent spawn,
``read_file`` / ``ls`` / ``glob`` / ``grep`` / ``edit_file`` /
``write_file`` for the virtual filesystem, ``execute`` for the sandbox).

We classify those tool names into AxonPush event types
(``AGENT_HANDOFF`` for sub-agents, ``AGENT_TOOL_CALL_*`` for the rest)
and propagate ``run_id`` / ``parent_run_id`` as ``span_id`` /
``parent_event_id``.

Tested against ``deepagents>=0.1.0,<2.0`` (Python >=3.11) and
``langchain-core>=0.1,<0.4``.

Install::

    pip install axonpush[deepagents]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import UUID

try:
    from deepagents import create_deep_agent as _create_deep_agent  # noqa: F401
    from deepagents.middleware.filesystem import (
        TOOLS_EXCLUDED_FROM_EVICTION as _FS_TOOLS,
    )
    from langchain_core.callbacks import AsyncCallbackHandler, BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError:
    raise ImportError(
        "Deep Agents integration requires the 'deepagents' extra. "
        "Install it with: pip install axonpush[deepagents]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._publisher import (
    AsyncBackgroundPublisher,
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    RqPublisher,
)
from axonpush.integrations._utils import (
    coerce_channel_id,
    derive_model_name,
    derive_runnable_name,
    extract_run_metadata,
    safe_serialize,
)
from axonpush.models import EventType

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

logger = logging.getLogger("axonpush")

_PLANNING_TOOLS = {"write_todos"}
_SUBAGENT_TOOLS = {"task"}
_FILESYSTEM_TOOLS = set(_FS_TOOLS)
_FILESYSTEM_READ_TOOLS = {"read_file", "ls", "glob", "grep"}
_SANDBOX_TOOLS = {"execute"}

_PublisherT = Union[BackgroundPublisher, RqPublisher, None]
_AsyncPublisherT = Union[AsyncBackgroundPublisher, RqPublisher, None]


def _build_sync_publisher(
    client: "AxonPush",
    mode: str,
    queue_size: int,
    shutdown_timeout: float,
    rq_options: Optional[Dict[str, Any]],
) -> _PublisherT:
    if mode == "rq":
        return RqPublisher(client, **(rq_options or {}))
    if mode == "background":
        return BackgroundPublisher(
            client,
            queue_size=queue_size,
            shutdown_timeout=shutdown_timeout,
        )
    return None


def _build_async_publisher(
    client: "AsyncAxonPush",
    mode: str,
    max_pending: int,
    rq_options: Optional[Dict[str, Any]],
) -> _AsyncPublisherT:
    if mode == "rq":
        return RqPublisher(client, **(rq_options or {}))
    if mode == "background":
        return AsyncBackgroundPublisher(client, max_pending=max_pending)
    return None


def _classify_tool_start(tool_name: str) -> Tuple[str, EventType]:
    if tool_name in _PLANNING_TOOLS:
        return "planning.update", EventType.AGENT_TOOL_CALL_START
    if tool_name in _SUBAGENT_TOOLS:
        return "subagent.spawn", EventType.AGENT_HANDOFF
    if tool_name in _FILESYSTEM_TOOLS:
        kind = "read" if tool_name in _FILESYSTEM_READ_TOOLS else "write"
        return f"filesystem.{kind}", EventType.AGENT_TOOL_CALL_START
    if tool_name in _SANDBOX_TOOLS:
        return "sandbox.execute", EventType.AGENT_TOOL_CALL_START
    return f"tool.{tool_name}.start", EventType.AGENT_TOOL_CALL_START


def _classify_tool_end(tool_name: str) -> Tuple[str, EventType]:
    if tool_name in _PLANNING_TOOLS:
        return "planning.complete", EventType.AGENT_TOOL_CALL_END
    if tool_name in _SUBAGENT_TOOLS:
        return "subagent.complete", EventType.AGENT_TOOL_CALL_END
    if tool_name in _FILESYSTEM_TOOLS:
        kind = "read" if tool_name in _FILESYSTEM_READ_TOOLS else "write"
        return f"filesystem.{kind}.complete", EventType.AGENT_TOOL_CALL_END
    if tool_name in _SANDBOX_TOOLS:
        return "sandbox.execute.complete", EventType.AGENT_TOOL_CALL_END
    return "tool.end", EventType.AGENT_TOOL_CALL_END


def _publish_kwargs(
    *,
    identifier: str,
    event_type: EventType,
    payload: Dict[str, Any],
    channel_id: str,
    agent_id: str,
    trace_id: str,
    span_id: str,
    metadata: Dict[str, Any],
    run_id: Optional[UUID],
    parent_run_id: Optional[UUID],
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if run_id is not None:
        span_id = str(run_id)
        metadata = {**metadata, "langchain_run_id": str(run_id)}
    if extra_metadata:
        metadata = {**metadata, **extra_metadata}
    out: Dict[str, Any] = {
        "identifier": identifier,
        "payload": payload,
        "channel_id": channel_id,
        "agent_id": agent_id,
        "trace_id": trace_id,
        "span_id": span_id,
        "event_type": event_type,
        "metadata": metadata,
    }
    if parent_run_id is not None:
        out["parent_event_id"] = str(parent_run_id)
        out["metadata"] = {
            **out["metadata"],
            "langchain_parent_run_id": str(parent_run_id),
        }
    return out


class AxonPushDeepAgentHandler(BaseCallbackHandler):
    """Sync DeepAgent callback handler that publishes to AxonPush."""

    def __init__(
        self,
        client: "AxonPush",
        channel_id: int | str,
        *,
        agent_id: str = "deepagent",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[Literal["background", "sync", "rq"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
        rq_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = coerce_channel_id(channel_id)
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)
        self._base_metadata: Dict[str, Any] = {
            **(metadata or {}),
            "framework": "deepagents",
        }
        self._publisher = _build_sync_publisher(
            client,
            mode or "background",
            queue_size,
            shutdown_timeout,
            rq_options,
        )

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.start",
            EventType.AGENT_START,
            {
                "chain_type": derive_runnable_name(serialized, kwargs),
                "inputs": safe_serialize(inputs),
            },
            run_id=run_id,
            parent_run_id=parent_run_id,
            extra_metadata=extract_run_metadata(kwargs),
        )

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.end",
            EventType.AGENT_END,
            {"outputs": safe_serialize(outputs)},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.error",
            EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.start",
            EventType.AGENT_START,
            {
                "model": derive_model_name(serialized, kwargs),
                "prompt_count": len(prompts),
            },
            run_id=run_id,
            parent_run_id=parent_run_id,
            extra_metadata=extract_run_metadata(kwargs),
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        gen_count = len(response.generations) if response.generations else 0
        self._publish(
            "llm.end",
            EventType.AGENT_END,
            {"generations": gen_count},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_llm_new_token(
        self,
        token: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.token",
            EventType.AGENT_LLM_TOKEN,
            {"token": token},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = (serialized or {}).get("name", "unknown")
        identifier, event_type = _classify_tool_start(tool_name)
        self._publish(
            identifier,
            event_type,
            {"tool_name": tool_name, "input": input_str[:2000]},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = name or "unknown"
        identifier, event_type = _classify_tool_end(tool_name)
        self._publish(
            identifier,
            event_type,
            {"tool_name": tool_name, "output": safe_serialize(output)},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.error",
            EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def _publish(
        self,
        identifier: str,
        event_type: EventType,
        payload: Dict[str, Any],
        *,
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            kwargs = _publish_kwargs(
                identifier=identifier,
                event_type=event_type,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                metadata=self._base_metadata,
                run_id=run_id,
                parent_run_id=parent_run_id,
                extra_metadata=extra_metadata,
            )
            if self._publisher is not None:
                self._publisher.submit(kwargs)
                return
            self._client.events.publish(**kwargs)
        except Exception:
            logger.warning(
                "AxonPush: failed to emit event %r, suppressing.",
                identifier,
                exc_info=True,
            )

    def flush(self, timeout: Optional[float] = None) -> None:
        if self._publisher is not None:
            self._publisher.flush(timeout)

    def close(self) -> None:
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None


class AsyncAxonPushDeepAgentHandler(AsyncCallbackHandler):
    """Async DeepAgent callback handler that publishes to AxonPush."""

    def __init__(
        self,
        client: "AsyncAxonPush",
        channel_id: int | str,
        *,
        agent_id: str = "deepagent",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[Literal["background", "sync", "rq"]] = None,
        max_pending: int = DEFAULT_QUEUE_SIZE,
        rq_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = coerce_channel_id(channel_id)
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)
        self._base_metadata: Dict[str, Any] = {
            **(metadata or {}),
            "framework": "deepagents",
        }
        self._publisher = _build_async_publisher(
            client,
            mode or "background",
            max_pending,
            rq_options,
        )

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.start",
            EventType.AGENT_START,
            {
                "chain_type": derive_runnable_name(serialized, kwargs),
                "inputs": safe_serialize(inputs),
            },
            run_id=run_id,
            parent_run_id=parent_run_id,
            extra_metadata=extract_run_metadata(kwargs),
        )

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.end",
            EventType.AGENT_END,
            {"outputs": safe_serialize(outputs)},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.error",
            EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.start",
            EventType.AGENT_START,
            {
                "model": derive_model_name(serialized, kwargs),
                "prompt_count": len(prompts),
            },
            run_id=run_id,
            parent_run_id=parent_run_id,
            extra_metadata=extract_run_metadata(kwargs),
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        gen_count = len(response.generations) if response.generations else 0
        self._publish(
            "llm.end",
            EventType.AGENT_END,
            {"generations": gen_count},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_llm_new_token(
        self,
        token: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.token",
            EventType.AGENT_LLM_TOKEN,
            {"token": token},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = (serialized or {}).get("name", "unknown")
        identifier, event_type = _classify_tool_start(tool_name)
        self._publish(
            identifier,
            event_type,
            {"tool_name": tool_name, "input": input_str[:2000]},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = name or "unknown"
        identifier, event_type = _classify_tool_end(tool_name)
        self._publish(
            identifier,
            event_type,
            {"tool_name": tool_name, "output": safe_serialize(output)},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.error",
            EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id,
            parent_run_id=parent_run_id,
        )

    def _publish(
        self,
        identifier: str,
        event_type: EventType,
        payload: Dict[str, Any],
        *,
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            kwargs = _publish_kwargs(
                identifier=identifier,
                event_type=event_type,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                metadata=self._base_metadata,
                run_id=run_id,
                parent_run_id=parent_run_id,
                extra_metadata=extra_metadata,
            )
            if self._publisher is not None:
                self._publisher.submit(kwargs)
                return
            logger.warning(
                "AxonPush: async handler in sync mode — event %r dropped.",
                identifier,
            )
        except Exception:
            logger.warning(
                "AxonPush: failed to emit event %r, suppressing.",
                identifier,
                exc_info=True,
            )

    async def aflush(self, timeout: Optional[float] = None) -> None:
        if isinstance(self._publisher, AsyncBackgroundPublisher):
            await self._publisher.flush(timeout)
        elif self._publisher is not None:
            self._publisher.flush(timeout)

    async def aclose(self) -> None:
        if isinstance(self._publisher, AsyncBackgroundPublisher):
            await self._publisher.aclose()
        elif self._publisher is not None:
            self._publisher.close()
        self._publisher = None

    def flush(self, timeout: Optional[float] = None) -> None:
        if isinstance(self._publisher, RqPublisher):
            self._publisher.flush(timeout)

    def close(self) -> None:
        if isinstance(self._publisher, RqPublisher):
            self._publisher.close()
            self._publisher = None


def get_deepagent_handler(
    client: "AxonPush | AsyncAxonPush",
    channel_id: int | str,
    **kwargs: Any,
) -> "AxonPushDeepAgentHandler | AsyncAxonPushDeepAgentHandler":
    """Pick the right handler class based on whether ``client`` is async."""
    from axonpush.client import AsyncAxonPush

    if isinstance(client, AsyncAxonPush):
        return AsyncAxonPushDeepAgentHandler(client, channel_id, **kwargs)
    return AxonPushDeepAgentHandler(client, channel_id, **kwargs)
