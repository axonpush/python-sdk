"""
02 — Agent Tracing

Simulate a research agent running a multi-step task.
All events share a trace_id so you can reconstruct the full execution.
Run: uv run 02_agent_tracing.py
"""

import time

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush, EventType
from axonpush._tracing import get_or_create_trace


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="tracing-demo")
        channel = client.channels.create(name="research", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        trace = get_or_create_trace()
        trace_id = trace.trace_id
        agent_id = "research-agent"

        print(f"Trace ID: {trace_id}\n")

        # Step 1: Agent starts
        client.events.publish(
            identifier="research.start",
            payload={"goal": "Find recent papers on transformer architectures"},
            channel_id=channel.id, agent_id=agent_id, trace_id=trace_id,
            span_id=trace.next_span_id(), event_type=EventType.AGENT_START,
        )
        print("[agent.start] Research agent started")
        time.sleep(0.3)

        # Step 2: Tool call — web search
        client.events.publish(
            identifier="web_search",
            payload={"query": "transformer architecture papers 2025", "engine": "google_scholar"},
            channel_id=channel.id, agent_id=agent_id, trace_id=trace_id,
            span_id=trace.next_span_id(), event_type=EventType.AGENT_TOOL_CALL_START,
            metadata={"tool_name": "web_search"},
        )
        print("[tool_call.start] Searching: 'transformer architecture papers 2025'")
        time.sleep(0.5)

        # Step 3: Tool call result
        client.events.publish(
            identifier="web_search",
            payload={"results": [
                {"title": "Attention Is Still All You Need", "year": 2025},
                {"title": "Sparse Transformers at Scale", "year": 2025},
            ], "count": 2},
            channel_id=channel.id, agent_id=agent_id, trace_id=trace_id,
            span_id=trace.next_span_id(), event_type=EventType.AGENT_TOOL_CALL_END,
            metadata={"tool_name": "web_search"},
        )
        print("[tool_call.end] Found 2 papers")
        time.sleep(0.3)

        # Step 4: Agent message
        client.events.publish(
            identifier="summary",
            payload={"message": "Found 2 relevant papers on transformer architectures from 2025."},
            channel_id=channel.id, agent_id=agent_id, trace_id=trace_id,
            span_id=trace.next_span_id(), event_type=EventType.AGENT_MESSAGE,
        )
        print("[agent.message] Generated summary")
        time.sleep(0.2)

        # Step 5: Agent ends
        client.events.publish(
            identifier="research.end",
            payload={"status": "success", "papers_found": 2},
            channel_id=channel.id, agent_id=agent_id, trace_id=trace_id,
            span_id=trace.next_span_id(), event_type=EventType.AGENT_END,
        )
        print("[agent.end] Research complete\n")

        # Fetch trace summary
        time.sleep(0.5)
        summary = client.traces.get_summary(trace_id)
        print("--- Trace Summary ---")
        print(f"  Trace ID:    {summary.trace_id}")
        print(f"  Events:      {summary.event_count}")
        print(f"  Agents:      {summary.agents}")
        print(f"  Duration:    {summary.duration_ms}ms")
        print(f"  Tool calls:  {summary.tool_call_count}")
        print(f"  Errors:      {summary.error_count}")

        # Clean up
        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
