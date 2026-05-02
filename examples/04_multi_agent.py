"""04 — Multi-agent handoff.

A planner agent delegates work to an executor agent. Both agents share the
same ``trace_id`` so the backend assembles the full execution path into one
trace, and we get a single summary at the end.

Run::

    uv run examples/04_multi_agent.py
"""

import time

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush, EventType, get_or_create_trace  # noqa: E402


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="multi-agent-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("pipeline", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        trace = get_or_create_trace()
        print(f"Trace: {trace.trace_id}\n")

        def emit(agent_id: str, identifier: str, payload: dict, event_type: EventType, **extra: object) -> None:
            client.events.publish(
                identifier, payload, channel_id,
                agent_id=agent_id,
                trace_id=trace.trace_id,
                span_id=trace.next_span_id(),
                event_type=event_type,
                **extra,
            )
            print(f"  [{agent_id}] {event_type.value}: {identifier}")

        emit("planner", "plan.start",
             {"task": "Write a blog post about AI safety"},
             EventType.AGENT_START)
        time.sleep(0.2)
        emit("planner", "plan.outline",
             {"outline": ["Introduction", "Key risks", "Mitigation", "Conclusion"]},
             EventType.AGENT_MESSAGE)
        time.sleep(0.2)
        emit("planner", "handoff",
             {"target_agent": "executor", "task": "Write sections from outline"},
             EventType.AGENT_HANDOFF,
             metadata={"from_agent": "planner", "to_agent": "executor"})
        time.sleep(0.2)
        emit("planner", "plan.end", {"status": "delegated"}, EventType.AGENT_END)
        time.sleep(0.3)

        emit("executor", "write.start", {"sections": 4}, EventType.AGENT_START)
        time.sleep(0.2)
        emit("executor", "web_search",
             {"query": "AI safety current research 2026"},
             EventType.AGENT_TOOL_CALL_START,
             metadata={"tool_name": "web_search"})
        time.sleep(0.4)
        emit("executor", "web_search",
             {"results_count": 8},
             EventType.AGENT_TOOL_CALL_END,
             metadata={"tool_name": "web_search"})
        time.sleep(0.2)
        emit("executor", "write.draft",
             {"word_count": 1200, "sections_written": 4},
             EventType.AGENT_MESSAGE)
        time.sleep(0.2)
        emit("executor", "write.end",
             {"status": "success", "word_count": 1200},
             EventType.AGENT_END)

        time.sleep(0.5)
        summary = client.traces.summary(trace.trace_id)
        if summary is not None:
            print("\n--- Trace Summary ---")
            print(f"  Trace ID:    {summary.trace_id}")
            print(f"  Agents:      {', '.join(summary.agents)}")
            print(f"  Events:      {int(summary.event_count)}")
            print(f"  Duration:    {summary.duration:.0f}ms")
            print(f"  Handoffs:    {int(summary.handoff_count)}")
            print(f"  Tool calls:  {int(summary.tool_call_count)}")
            print(f"  Errors:      {int(summary.error_count)}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
