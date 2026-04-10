"""Anthropic/Claude integration for AxonPush.

Requires: ``pip install axonpush[anthropic]``

Unlike LangChain/CrewAI, the Anthropic SDK has no callback hooks. This
integration wraps ``messages.create()`` calls to automatically emit events
for tool_use blocks, text responses, and conversation turns.

Usage::

    from axonpush import AxonPush
    from axonpush.integrations.anthropic import AxonPushAnthropicTracer

    client = AxonPush(api_key="ak_...", tenant_id="1")
    tracer = AxonPushAnthropicTracer(client, channel_id=1)

    # Sync
    response = tracer.create_message(
        anthropic_client,
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hello"}],
        tools=[...],
    )

    # Async
    response = await tracer.acreate_message(async_anthropic_client, ...)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

try:
    import anthropic  # noqa: F401 — verify the package is installed
except ImportError:
    raise ImportError(
        "Anthropic integration requires the 'anthropic' extra. "
        "Install it with: pip install axonpush[anthropic]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.models.events import EventType

logger = logging.getLogger("axonpush")

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush, AxonPush


class AxonPushAnthropicTracer:
    """Wraps Anthropic API calls to emit AxonPush trace events."""

    def __init__(
        self,
        client: AxonPush | AsyncAxonPush,
        channel_id: int,
        *,
        agent_id: str = "claude",
        trace_id: Optional[str] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)

    def create_message(self, anthropic_client: Any, **kwargs: Any) -> Any:
        """Wrap a sync ``anthropic_client.messages.create()`` call with tracing."""
        self._emit_sync(
            "conversation.turn",
            EventType.AGENT_START,
            {
                "model": kwargs.get("model"),
                "message_count": len(kwargs.get("messages", [])),
            },
        )

        response = anthropic_client.messages.create(**kwargs)
        self._process_response(response)
        return response

    async def acreate_message(self, anthropic_client: Any, **kwargs: Any) -> Any:
        """Wrap an async ``anthropic_client.messages.create()`` call with tracing."""
        await self._emit_async(
            "conversation.turn",
            EventType.AGENT_START,
            {
                "model": kwargs.get("model"),
                "message_count": len(kwargs.get("messages", [])),
            },
        )

        response = await anthropic_client.messages.create(**kwargs)
        await self._aprocess_response(response)
        return response

    def send_tool_result(self, tool_use_id: str, result: Any) -> None:
        """Emit a tool_call.end event when you send a tool result back."""
        self._emit_sync(
            "tool.result",
            EventType.AGENT_TOOL_CALL_END,
            {"tool_use_id": tool_use_id, "result_preview": str(result)[:500]},
        )

    async def asend_tool_result(self, tool_use_id: str, result: Any) -> None:
        """Async variant of send_tool_result."""
        await self._emit_async(
            "tool.result",
            EventType.AGENT_TOOL_CALL_END,
            {"tool_use_id": tool_use_id, "result_preview": str(result)[:500]},
        )

    # -- Internal --

    def _process_response(self, response: Any) -> None:
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", None)
            if block_type == "tool_use":
                self._emit_sync(
                    f"tool.{block.name}.start",
                    EventType.AGENT_TOOL_CALL_START,
                    {
                        "tool_name": block.name,
                        "tool_use_id": block.id,
                        "input": _truncate(block.input),
                    },
                )
            elif block_type == "text":
                self._emit_sync(
                    "agent.response",
                    EventType.AGENT_MESSAGE,
                    {"text_length": len(block.text)},
                )

    async def _aprocess_response(self, response: Any) -> None:
        for block in getattr(response, "content", []):
            block_type = getattr(block, "type", None)
            if block_type == "tool_use":
                await self._emit_async(
                    f"tool.{block.name}.start",
                    EventType.AGENT_TOOL_CALL_START,
                    {
                        "tool_name": block.name,
                        "tool_use_id": block.id,
                        "input": _truncate(block.input),
                    },
                )
            elif block_type == "text":
                await self._emit_async(
                    "agent.response",
                    EventType.AGENT_MESSAGE,
                    {"text_length": len(block.text)},
                )

    def _emit_sync(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any]
    ) -> None:
        try:
            self._client.events.publish(  # type: ignore[union-attr]
                identifier=identifier,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "anthropic"},
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)

    async def _emit_async(
        self, identifier: str, event_type: EventType, payload: Dict[str, Any]
    ) -> None:
        try:
            await self._client.events.publish(  # type: ignore[union-attr]
                identifier=identifier,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "anthropic"},
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)


def _truncate(obj: Any, max_len: int = 500) -> Any:
    s = str(obj)
    return s[:max_len] if len(s) > max_len else s
