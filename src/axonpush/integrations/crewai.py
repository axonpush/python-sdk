"""CrewAI integration for AxonPush.

Requires: ``pip install axonpush[crewai]``

Usage::

    from axonpush import AxonPush
    from axonpush.integrations.crewai import AxonPushCrewCallbacks

    client = AxonPush(api_key="ak_...", tenant_id="1")
    callbacks = AxonPushCrewCallbacks(client, channel_id=1)

    callbacks.on_crew_start()
    crew = Crew(
        agents=[...],
        tasks=[...],
        step_callback=callbacks.on_step,
        task_callback=callbacks.on_task_complete,
    )
    result = crew.kickoff()
    callbacks.on_crew_end(result)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from axonpush._tracing import get_or_create_trace
from axonpush.models.events import EventType

logger = logging.getLogger("axonpush")

if TYPE_CHECKING:
    from axonpush.client import AxonPush


class AxonPushCrewCallbacks:
    """CrewAI step and task callbacks that publish events to AxonPush."""

    def __init__(
        self,
        client: AxonPush,
        channel_id: int,
        *,
        agent_id: str = "crewai",
        trace_id: Optional[str] = None,
    ) -> None:
        self._client = client
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)

    def on_crew_start(self) -> None:
        """Call manually before ``crew.kickoff()``."""
        self._publish(
            "crew.start",
            EventType.AGENT_START,
            {"framework": "crewai"},
        )

    def on_step(self, step_output: Any) -> None:
        """Pass as ``step_callback`` to ``Crew(...)``."""
        agent_name = str(getattr(step_output, "agent", self._agent_id))
        tool = getattr(step_output, "tool", None)

        if tool:
            tool_name = str(tool)
            self._publish(
                f"tool.{tool_name}.start",
                EventType.AGENT_TOOL_CALL_START,
                {
                    "tool_name": tool_name,
                    "tool_input": str(getattr(step_output, "tool_input", ""))[:500],
                },
                agent_id=agent_name,
            )

            result = getattr(step_output, "result", None)
            if result is not None:
                self._publish(
                    f"tool.{tool_name}.end",
                    EventType.AGENT_TOOL_CALL_END,
                    {
                        "tool_name": tool_name,
                        "result_preview": str(result)[:500],
                    },
                    agent_id=agent_name,
                )
        else:
            self._publish(
                "agent.step",
                EventType.AGENT_MESSAGE,
                {"thought": str(getattr(step_output, "thought", ""))[:500]},
                agent_id=agent_name,
            )

    def on_task_complete(self, task_output: Any) -> None:
        """Pass as ``task_callback`` to ``Crew(...)``."""
        self._publish(
            "task.complete",
            EventType.AGENT_END,
            {
                "task_description": str(getattr(task_output, "description", ""))[:200],
                "output_preview": str(task_output)[:500],
            },
        )

    def on_crew_end(self, result: Any = None) -> None:
        """Call manually after ``crew.kickoff()`` returns."""
        self._publish(
            "crew.end",
            EventType.AGENT_END,
            {"result_preview": str(result)[:500] if result else None},
        )

    def _publish(
        self,
        identifier: str,
        event_type: EventType,
        payload: Dict[str, Any],
        *,
        agent_id: Optional[str] = None,
    ) -> None:
        try:
            self._client.events.publish(
                identifier=identifier,
                payload=payload,
                channel_id=self._channel_id,
                agent_id=agent_id or self._agent_id,
                trace_id=self._trace.trace_id,
                span_id=self._trace.next_span_id(),
                event_type=event_type,
                metadata={"framework": "crewai"},
            )
        except Exception:
            logger.warning("AxonPush: failed to emit event %r, suppressing.", identifier, exc_info=True)
