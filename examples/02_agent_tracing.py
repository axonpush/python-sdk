"""02 — Agent tracing.

Walk a research agent through a multi-step task. Every event shares a
``trace_id`` so the backend can stitch them back into a single trace and
return a summary at the end.

Run::

    uv run examples/02_agent_tracing.py
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
            app = client.apps.create(name="tracing-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("research", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        trace = get_or_create_trace()
        agent_id = "research-agent"
        print(f"Trace: {trace.trace_id}\n")

        def emit(identifier: str, payload: dict, event_type: EventType, **extra: object) -> None:
            client.events.publish(
                identifier, payload, channel_id,
                agent_id=agent_id,
                trace_id=trace.trace_id,
                span_id=trace.next_span_id(),
                event_type=event_type,
                **extra,
            )

        emit("research.start",
             {"goal": "Find recent papers on transformer architectures"},
             EventType.AGENT_START)
        print("[start] research agent started")
        time.sleep(0.2)

        emit("web_search",
             {"query": "transformer architecture papers 2026", "engine": "google_scholar"},
             EventType.AGENT_TOOL_CALL_START,
             metadata={"tool_name": "web_search"})
        print("[tool_call.start] searching")
        time.sleep(0.4)

        emit("web_search",
             {"results": [
                 {"title": "Attention Is Still All You Need", "year": 2026},
                 {"title": "Sparse Transformers at Scale", "year": 2026},
             ], "count": 2},
             EventType.AGENT_TOOL_CALL_END,
             metadata={"tool_name": "web_search"})
        print("[tool_call.end] found 2 papers")
        time.sleep(0.2)

        emit("summary",
             {"message": "Found 2 relevant papers on transformer architectures from 2026."},
             EventType.AGENT_MESSAGE)
        print("[agent.message] summary generated")
        time.sleep(0.2)

        emit("research.end",
             {"status": "success", "papers_found": 2},
             EventType.AGENT_END)
        print("[end] research complete\n")

        # Backend ingest is eventually consistent — give it a beat before
        # asking for the trace summary.
        time.sleep(0.5)
        summary = client.traces.summary(trace.trace_id)
        if summary is not None:
            print("--- Trace Summary ---")
            print(f"  Trace ID:     {summary.trace_id}")
            print(f"  Events:       {int(summary.event_count)}")
            print(f"  Agents:       {summary.agents}")
            print(f"  Duration:     {summary.duration:.0f}ms")
            print(f"  Tool calls:   {int(summary.tool_call_count)}")
            print(f"  Errors:       {int(summary.error_count)}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
