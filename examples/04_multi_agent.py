"""
04 — Multi-Agent Handoff

Simulate a planner agent that delegates to an executor agent.
Both agents share a trace_id so you can see the full execution flow.
Run: uv run 04_multi_agent.py
"""

import time

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush, EventType
from axonpush._tracing import get_or_create_trace


def publish(client, channel_id, trace_id, trace, agent_id, identifier, payload, event_type, **kwargs):
    client.events.publish(
        identifier=identifier, payload=payload, channel_id=channel_id,
        agent_id=agent_id, trace_id=trace_id, span_id=trace.next_span_id(),
        event_type=event_type, **kwargs,
    )
    print(f"  [{agent_id}] {event_type.value}: {identifier}")


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="multi-agent-demo")
        channel = client.channels.create(name="pipeline", app_id=app.id)

        trace = get_or_create_trace()
        trace_id = trace.trace_id
        print(f"Trace: {trace_id}\n")

        # --- Planner Agent ---
        publish(client, channel.id, trace_id, trace, "planner",
                "plan.start", {"task": "Write a blog post about AI safety"}, EventType.AGENT_START)
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "planner",
                "plan.outline", {"outline": ["Introduction", "Key risks", "Mitigation", "Conclusion"]},
                EventType.AGENT_MESSAGE)
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "planner",
                "handoff", {"target_agent": "executor", "task": "Write sections from outline"},
                EventType.AGENT_HANDOFF,
                metadata={"from_agent": "planner", "to_agent": "executor"})
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "planner",
                "plan.end", {"status": "delegated"}, EventType.AGENT_END)
        time.sleep(0.3)

        # --- Executor Agent ---
        publish(client, channel.id, trace_id, trace, "executor",
                "write.start", {"sections": 4}, EventType.AGENT_START)
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "executor",
                "web_search", {"query": "AI safety current research 2025"},
                EventType.AGENT_TOOL_CALL_START, metadata={"tool_name": "web_search"})
        time.sleep(0.4)

        publish(client, channel.id, trace_id, trace, "executor",
                "web_search", {"results_count": 8},
                EventType.AGENT_TOOL_CALL_END, metadata={"tool_name": "web_search"})
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "executor",
                "write.draft", {"word_count": 1200, "sections_written": 4},
                EventType.AGENT_MESSAGE)
        time.sleep(0.2)

        publish(client, channel.id, trace_id, trace, "executor",
                "write.end", {"status": "success", "word_count": 1200}, EventType.AGENT_END)

        # Fetch trace summary
        time.sleep(0.5)
        print()
        summary = client.traces.get_summary(trace_id)
        print("--- Trace Summary ---")
        print(f"  Trace ID:    {summary.trace_id}")
        print(f"  Agents:      {', '.join(summary.agents)}")
        print(f"  Total events: {summary.event_count}")
        print(f"  Duration:    {summary.duration_ms}ms")
        print(f"  Handoffs:    {summary.handoff_count}")
        print(f"  Tool calls:  {summary.tool_call_count}")
        print(f"  Errors:      {summary.error_count}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
