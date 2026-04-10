"""OpenAI Agents SDK integration for AxonPush.

Requires: ``pip install axonpush[openai-agents]``

Usage::

    from axonpush import AsyncAxonPush
    from axonpush.integrations.openai_agents import AxonPushRunHooks

    client = AsyncAxonPush(api_key="ak_...", tenant_id="1")
    hooks = AxonPushRunHooks(client, channel_id=1)
    result = await Runner.run(agent, input="...", hooks=hooks)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

try:
    from agents import Agent, RunContextWrapper, RunHooks, Tool
except ImportError:
    raise ImportError(
        "OpenAI Agents integration requires the 'openai-agents' extra. "
        "Install it with: pip install axonpush[openai-agents]"
    ) from None

from axonpush._tracing import get_or_create_trace
from axonpush.models.events import EventType

logger = logging.getLogger("axonpush")

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush


class AxonPushRunHooks(RunHooks[Any]):
    """OpenAI Agents SDK lifecycle hooks that publish events to AxonPush."""

    def __init__(
        self,
        client: AsyncAxonPush,
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._default_agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)

    async def on_agent_start(
        self, context: RunContextWrapper[Any], agent: Agent[Any]
    ) -> None:
        agent_name = getattr(agent, "name", None) or self._default_agent_id or "openai-agent"
        await self._publish(
            "agent.run.start",
            EventType.AGENT_START,
            {"agent_name": agent_name, "model": getattr(agent, "model", None)},
            agent_id=agent_name,
        )

    async def on_agent_end(
        self, context: RunContextWrapper[Any], agent: Agent[Any], output: str
    ) -> None:
        agent_name = getattr(agent, "name", None) or self._default_agent_id or "openai-agent"
        await self._publish(
            "agent.run.end",
            EventType.AGENT_END,
            {"agent_name": agent_name, "output_length": len(output)},
            agent_id=agent_name,
        )

    async def on_tool_start(
        self, context: RunContextWrapper[Any], agent: Agent[Any], tool: Tool
    ) -> None:
        agent_name = getattr(agent, "name", None) or "openai-agent"
        tool_name = getattr(tool, "name", "unknown")
        await self._publish(
            f"tool.{tool_name}.start",
            EventType.AGENT_TOOL_CALL_START,
            {"tool_name": tool_name, "agent_name": agent_name},
            agent_id=agent_name,
        )

    async def on_tool_end(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        tool: Tool,
        result: str,
    ) -> None:
        agent_name = getattr(agent, "name", None) or "openai-agent"
        tool_name = getattr(tool, "name", "unknown")
        await self._publish(
            f"tool.{tool_name}.end",
            EventType.AGENT_TOOL_CALL_END,
            {"tool_name": tool_name, "result_length": len(result)},
            agent_id=agent_name,
        )

    async def on_handoff(
        self,
        context: RunContextWrapper[Any],
        from_agent: Agent[Any],
        to_agent: Agent[Any],
    ) -> None:
        from_name = getattr(from_agent, "name", None) or "openai-agent"
        to_name = getattr(to_agent, "name", None) or "openai-agent"
        await self._publish(
            "agent.handoff",
            EventType.AGENT_HANDOFF,
            {"from_agent": from_name, "to_agent": to_name},
            agent_id=from_name,
        )

    async def _publish(
        self,
        identifier: str,
        event_type: EventType,
        payload: Dict[str, Any],
        *,
        agent_id: Optional[str] = None,
    ) -> None:
        try:
            await self._client.events.publish(
                identifier=identifier,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=agent_id or self._default_agent_id or "openai-agent",
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "openai-agents"},
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)
