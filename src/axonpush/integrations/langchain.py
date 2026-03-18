"""LangChain/LangGraph integration for AxonPush.

Requires: ``pip install axonpush[langchain]``

Usage::

    from axonpush import AxonPush
    from axonpush.integrations.langchain import AxonPushCallbackHandler

    client = AxonPush(api_key="ak_...", tenant_id="1")
    handler = AxonPushCallbackHandler(client, channel_id=1, agent_id="my-agent")
    chain.invoke({"input": "..."}, config={"callbacks": [handler]})
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import UUID

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError:
    raise ImportError(
        "LangChain integration requires the 'langchain' extra. "
        "Install it with: pip install axonpush[langchain]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.models.events import EventType

# Use TYPE_CHECKING to avoid circular import issues with the client
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axonpush.client import AxonPush


class AxonPushCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that publishes lifecycle events to AxonPush."""

    def __init__(
        self,
        client: AxonPush,
        channel_id: int,
        *,
        agent_id: str = "langchain",
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)
        self._base_metadata: Dict[str, Any] = {**(metadata or {}), "framework": "langchain"}

    # -- Chain lifecycle --

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
            {"chain_type": serialized.get("name", "unknown"), "inputs": _safe(inputs)},
            run_id=run_id,
            parent_run_id=parent_run_id,
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
            {"outputs": _safe(outputs)},
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

    # -- LLM lifecycle --

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
            {"model": serialized.get("name", "unknown"), "prompt_count": len(prompts)},
            run_id=run_id,
            parent_run_id=parent_run_id,
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

    # -- Tool lifecycle --

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown")
        self._publish(
            f"tool.{tool_name}.start",
            EventType.AGENT_TOOL_CALL_START,
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
        **kwargs: Any,
    ) -> None:
        self._publish(
            "tool.end",
            EventType.AGENT_TOOL_CALL_END,
            {"output": _safe(output)},
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

    # -- Internal --

    def _publish(
        self,
        identifier: str,
        event_type: EventType,
        payload: Dict[str, Any],
        *,
        run_id: Optional[UUID] = None,
        parent_run_id: Optional[UUID] = None,
    ) -> None:
        meta = {**self._base_metadata}
        if run_id:
            meta["langchain_run_id"] = str(run_id)
        if parent_run_id:
            meta["langchain_parent_run_id"] = str(parent_run_id)

        self._client.events.publish(
            identifier=identifier,
            payload=payload,
            channel_id=self._channel_id,
            agent_id=self._agent_id,
            trace_id=self._trace.trace_id,
            span_id=self._trace.next_span_id(),
            event_type=event_type,
            metadata=meta,
        )


def _safe(obj: Any, max_len: int = 2000) -> Any:
    """Attempt JSON-safe serialization, truncating large values."""
    try:
        s = json.dumps(obj, default=str)
        if len(s) > max_len:
            return json.loads(s[:max_len] + "...")
        return json.loads(s)
    except (TypeError, ValueError):
        result = str(obj)
        return result[:max_len]
