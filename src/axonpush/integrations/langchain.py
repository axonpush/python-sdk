from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

try:
    from langchain_core.callbacks import AsyncCallbackHandler, BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError:
    raise ImportError(
        "LangChain integration requires the 'langchain' extra. "
        "Install it with: pip install axonpush[langchain]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._publisher import (
    AsyncBackgroundPublisher,
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    RqPublisher,
)
from axonpush.integrations._utils import safe_serialize
from axonpush.models.events import EventType

logger = logging.getLogger("axonpush")

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush

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
            client, queue_size=queue_size, shutdown_timeout=shutdown_timeout,
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


class AxonPushCallbackHandler(BaseCallbackHandler):

    def __init__(
        self,
        client: "AxonPush",
        channel_id: int,
        *,
        agent_id: str = "langchain",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[Literal["background", "sync", "rq"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
        rq_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)
        self._base_metadata: Dict[str, Any] = {**(metadata or {}), "framework": "langchain"}
        self._publisher = _build_sync_publisher(
            client, mode or "background", queue_size, shutdown_timeout, rq_options,
        )

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.start", EventType.AGENT_START,
            {"chain_type": (serialized or {}).get("name", "unknown"), "inputs": safe_serialize(inputs)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_chain_end(
        self, outputs: Dict[str, Any],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.end", EventType.AGENT_END,
            {"outputs": safe_serialize(outputs)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_chain_error(
        self, error: BaseException,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.error", EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.start", EventType.AGENT_START,
            {"model": (serialized or {}).get("name", "unknown"), "prompt_count": len(prompts)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_llm_end(
        self, response: LLMResult,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        gen_count = len(response.generations) if response.generations else 0
        self._publish(
            "llm.end", EventType.AGENT_END,
            {"generations": gen_count},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_llm_new_token(
        self, token: str,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.token", EventType.AGENT_LLM_TOKEN,
            {"token": token},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        tool_name = (serialized or {}).get("name", "unknown")
        self._publish(
            f"tool.{tool_name}.start", EventType.AGENT_TOOL_CALL_START,
            {"tool_name": tool_name, "input": input_str[:2000]},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_tool_end(
        self, output: Any,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.end", EventType.AGENT_TOOL_CALL_END,
            {"output": safe_serialize(output)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def on_tool_error(
        self, error: BaseException,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.error", EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def _publish(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any],
        *, run_id: Optional[UUID] = None, parent_run_id: Optional[UUID] = None,
    ) -> None:
        try:
            meta = {**self._base_metadata}
            if run_id:
                meta["langchain_run_id"] = str(run_id)
            if parent_run_id:
                meta["langchain_parent_run_id"] = str(parent_run_id)

            publish_kwargs: Dict[str, Any] = {
                "identifier": identifier,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": self._agent_id,
                "trace_id": self._trace.trace_id,
                "span_id": self._trace.next_span_id(),
                "event_type": event_type,
                "metadata": meta,
            }

            if self._publisher is not None:
                self._publisher.submit(publish_kwargs)
                return

            self._client.events.publish(**publish_kwargs)
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)

    def flush(self, timeout: Optional[float] = None) -> None:
        if self._publisher is not None:
            self._publisher.flush(timeout)

    def close(self) -> None:
        if self._publisher is not None:
            self._publisher.close()
            self._publisher = None


class AsyncAxonPushCallbackHandler(AsyncCallbackHandler):

    def __init__(
        self,
        client: "AsyncAxonPush",
        channel_id: int,
        *,
        agent_id: str = "langchain",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mode: Optional[Literal["background", "sync", "rq"]] = None,
        max_pending: int = DEFAULT_QUEUE_SIZE,
        rq_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)
        self._base_metadata: Dict[str, Any] = {**(metadata or {}), "framework": "langchain"}
        self._publisher = _build_async_publisher(
            client, mode or "background", max_pending, rq_options,
        )

    async def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.start", EventType.AGENT_START,
            {"chain_type": (serialized or {}).get("name", "unknown"), "inputs": safe_serialize(inputs)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_chain_end(
        self, outputs: Dict[str, Any],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.end", EventType.AGENT_END,
            {"outputs": safe_serialize(outputs)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_chain_error(
        self, error: BaseException,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "chain.error", EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str],
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.start", EventType.AGENT_START,
            {"model": (serialized or {}).get("name", "unknown"), "prompt_count": len(prompts)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_llm_end(
        self, response: LLMResult,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        gen_count = len(response.generations) if response.generations else 0
        self._publish(
            "llm.end", EventType.AGENT_END,
            {"generations": gen_count},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_llm_new_token(
        self, token: str,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "llm.token", EventType.AGENT_LLM_TOKEN,
            {"token": token},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        tool_name = (serialized or {}).get("name", "unknown")
        self._publish(
            f"tool.{tool_name}.start", EventType.AGENT_TOOL_CALL_START,
            {"tool_name": tool_name, "input": input_str[:2000]},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_tool_end(
        self, output: Any,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.end", EventType.AGENT_TOOL_CALL_END,
            {"output": safe_serialize(output)},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    async def on_tool_error(
        self, error: BaseException,
        *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.error", EventType.AGENT_ERROR,
            {"error": str(error), "error_type": type(error).__name__},
            run_id=run_id, parent_run_id=parent_run_id,
        )

    def _publish(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any],
        *, run_id: Optional[UUID] = None, parent_run_id: Optional[UUID] = None,
    ) -> None:
        try:
            meta = {**self._base_metadata}
            if run_id:
                meta["langchain_run_id"] = str(run_id)
            if parent_run_id:
                meta["langchain_parent_run_id"] = str(parent_run_id)

            publish_kwargs: Dict[str, Any] = {
                "identifier": identifier,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": self._agent_id,
                "trace_id": self._trace.trace_id,
                "span_id": self._trace.next_span_id(),
                "event_type": event_type,
                "metadata": meta,
            }

            if self._publisher is not None:
                self._publisher.submit(publish_kwargs)
                return

            logger.warning(
                "AxonPush: async handler in sync mode — event %r published inline.", identifier,
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)

    async def aflush(self, timeout: Optional[float] = None) -> None:
        if isinstance(self._publisher, AsyncBackgroundPublisher):
            await self._publisher.flush(timeout)
        elif self._publisher is not None:
            self._publisher.flush(timeout)

    async def aclose(self) -> None:
        if isinstance(self._publisher, AsyncBackgroundPublisher):
            await self._publisher.close()
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


def get_langchain_handler(
    client: "AxonPush | AsyncAxonPush",
    channel_id: int,
    **kwargs: Any,
) -> "AxonPushCallbackHandler | AsyncAxonPushCallbackHandler":
    from axonpush.client import AsyncAxonPush

    if isinstance(client, AsyncAxonPush):
        return AsyncAxonPushCallbackHandler(client, channel_id, **kwargs)
    return AxonPushCallbackHandler(client, channel_id, **kwargs)
