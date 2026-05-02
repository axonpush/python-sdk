"""CrewAI integration for AxonPush.

Provides a step-callback bag (:class:`AxonPushCrewCallbacks`) that you
attach to a Crew's task / agent ``step_callback``. CrewAI's hook surface
between 0.50 and 0.90 has stayed largely stable: a single callable that
receives a step output object exposing ``agent``, ``tool``, ``tool_input``,
``result``, ``thought``. We code against attribute access only, so any
0.50+ release that exposes those names works.

Tested against ``crewai>=0.50.0,<2.0`` (Python >=3.11).

Install::

    pip install axonpush[crewai]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional

from axonpush._tracing import get_or_create_trace
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
)
from axonpush.integrations._utils import coerce_channel_id
from axonpush.models import EventType

if TYPE_CHECKING:
    from axonpush.client import AxonPush

logger = logging.getLogger("axonpush")


class AxonPushCrewCallbacks:
    """A bundle of step / task / crew callbacks for CrewAI."""

    def __init__(
        self,
        client: "AxonPush",
        channel_id: int | str,
        *,
        agent_id: str = "crewai",
        trace_id: Optional[str] = None,
        mode: Optional[Literal["background", "sync"]] = None,
        queue_size: int = DEFAULT_QUEUE_SIZE,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
    ) -> None:
        self._client = client
        self._channel_id = coerce_channel_id(channel_id)
        self._agent_id = agent_id
        self._trace = get_or_create_trace(trace_id)

        resolved_mode = mode or "background"
        if resolved_mode == "background":
            self._publisher: Optional[BackgroundPublisher] = BackgroundPublisher(
                client,
                queue_size=queue_size,
                shutdown_timeout=shutdown_timeout,
            )
        else:
            self._publisher = None

    def on_crew_start(self) -> None:
        self._publish("crew.start", EventType.AGENT_START, {"framework": "crewai"})

    def on_step(self, step_output: Any) -> None:
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
                    {"tool_name": tool_name, "result_preview": str(result)[:500]},
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
        self._publish(
            "task.complete",
            EventType.AGENT_END,
            {
                "task_description": str(getattr(task_output, "description", ""))[:200],
                "output_preview": str(task_output)[:500],
            },
        )

    def on_crew_end(self, result: Any = None) -> None:
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
            publish_kwargs: Dict[str, Any] = {
                "identifier": identifier,
                "payload": payload,
                "channel_id": self._channel_id,
                "agent_id": agent_id or self._agent_id,
                "trace_id": self._trace.trace_id,
                "span_id": self._trace.next_span_id(),
                "event_type": event_type,
                "metadata": {"framework": "crewai"},
            }
            if self._publisher is not None:
                self._publisher.submit(publish_kwargs)
                return
            self._client.events.publish(**publish_kwargs)
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
