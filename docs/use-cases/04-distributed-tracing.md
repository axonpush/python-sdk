# Trace a Multi-Step Agent Run End-to-End

> Correlate every event in a single agent run with auto-generated trace and span IDs. Find where things went wrong without reading walls of logs.

## The Problem

Your agent runs 12 steps across 3 tool calls. Something went wrong at step 8. You have logs, but they're a wall of text with no correlation. You can't tell which events belong to the same run or what order they happened in. You need a trace ID that ties everything together.

## The Solution

```bash
pip install axonpush
```

```python
from axonpush import AxonPush, EventType, get_or_create_trace

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    # Create a trace — all events in this run share the same trace_id
    trace = get_or_create_trace()

    client.events.publish(
        "web_search", {"query": "AI frameworks"},
        channel_id=1, agent_id="researcher",
        trace_id=trace.trace_id, span_id=trace.next_span_id(),
        event_type=EventType.AGENT_TOOL_CALL_START,
    )

    client.events.publish(
        "summarize", {"input_tokens": 1200},
        channel_id=1, agent_id="researcher",
        trace_id=trace.trace_id, span_id=trace.next_span_id(),
        event_type=EventType.AGENT_TOOL_CALL_START,
    )

    # Get the full picture
    summary = client.traces.get_summary(trace.trace_id)
    print(f"Events: {summary.total_events}, Duration: {summary.duration_ms}ms")
    print(f"Errors: {summary.error_count}, Tool calls: {summary.tool_call_count}")
```

## What Just Happened

- `get_or_create_trace()` creates a `TraceContext` with an auto-generated `trace_id` (prefixed `tr_`).
- `trace.next_span_id()` generates sequential span IDs (`sp_<hex>_0001`, `sp_<hex>_0002`, ...) so you can see event order.
- Both events share the same `trace_id`, linking them as part of one run.
- `traces.get_summary()` returns analytics: total events, duration, error count, tool call count, handoff count, and the list of agents involved.
- No external tracing infrastructure needed — no Jaeger, no Datadog, no setup.

<details>
<summary><strong>Go Deeper</strong></summary>

### Query traces

```python
# List recent traces
traces = client.traces.list(page=1, limit=20)
for t in traces:
    print(f"{t.trace_id}: {t.event_count} events ({t.start_time} → {t.end_time})")

# Get all events in a trace, ordered
events = client.traces.get_events("tr_run_42")
for e in events:
    print(f"  [{e.span_id}] {e.identifier} ({e.event_type})")
```

### TraceSummary fields

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | `str` | The trace identifier |
| `total_events` | `int` | Number of events in the trace |
| `agents` | `List[str]` | Agent IDs that participated |
| `event_types` | `List[str]` | Event types that occurred |
| `start_time` | `datetime` | First event timestamp |
| `end_time` | `datetime` | Last event timestamp |
| `duration_ms` | `int` | Total trace duration |
| `error_count` | `int` | Number of error events |
| `tool_call_count` | `int` | Number of tool call events |
| `handoff_count` | `int` | Number of agent handoffs |
| `events` | `List[Event]` | All events in the trace |

### Cross-service correlation

Pass an explicit `trace_id` to correlate events across microservices:

```python
# Service A
trace = get_or_create_trace("tr_pipeline_run_99")
client_a.events.publish("step_a", {...}, channel_id=1, trace_id=trace.trace_id, ...)

# Service B — same trace_id, different channel
trace = get_or_create_trace("tr_pipeline_run_99")
client_b.events.publish("step_b", {...}, channel_id=2, trace_id=trace.trace_id, ...)

# Query the unified trace
summary = client.traces.get_summary("tr_pipeline_run_99")
# Shows events from both services
```

### How context propagation works

`get_or_create_trace()` uses Python's `contextvars` module. The trace context automatically propagates to:
- Other functions called in the same thread
- `asyncio` tasks spawned from the current task

This means you can call `get_or_create_trace()` once at the top of your agent run, and all downstream `events.publish()` calls can reference the same trace without passing it explicitly.

### Async variant

```python
from axonpush import AsyncAxonPush, get_or_create_trace

async with AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    trace = get_or_create_trace()

    await client.events.publish(
        "web_search", {"query": "AI agents"},
        channel_id=1, agent_id="researcher",
        trace_id=trace.trace_id, span_id=trace.next_span_id(),
        event_type=EventType.AGENT_TOOL_CALL_START,
    )

    summary = await client.traces.get_summary(trace.trace_id)
```

</details>

## Next Steps

- [Get notified when your agent fails (webhooks)](05-error-webhooks.md)
- [Stream events live with SSE](03-live-dashboard-sse.md)
- [Add framework integrations (auto-tracing included)](02-framework-integrations.md)
