# See What Your AI Agent Is Doing — In Real Time

> Publish structured events from your agent and query them instantly. The hello world of agent observability.

## The Problem

You built an AI agent. It runs for 30 seconds, returns a result, and you have no idea what happened in between. Did it call the right tools? Did it waste tokens on a dead-end? Without event-level visibility, debugging is guesswork.

## The Solution

```bash
pip install axonpush
```

```python
from axonpush import AxonPush, EventType

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.com") as client:
    # Publish an event when your agent calls a tool
    event = client.events.publish(
        "web_search",                              # what happened
        {"query": "AI agent frameworks", "results": 5},  # structured data
        channel_id=1,
        agent_id="researcher",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )

    print(f"Event {event.id} published at {event.created_at}")

    # Pull the last 10 events from this channel
    events = client.events.list(channel_id=1, limit=10)
    for e in events:
        print(f"[{e.agent_id}] {e.identifier}: {e.payload}")
```

## What Just Happened

- You created a client with your API key and tenant ID. The `with` block ensures cleanup.
- `events.publish()` sent a structured event to channel 1. The `identifier` names the action, `payload` carries the data.
- `EventType.AGENT_TOOL_CALL_START` tags this event so dashboards and filters know it's a tool invocation.
- `events.list()` retrieved recent events from the same channel — useful for debugging or building a replay view.
- The returned `Event` object includes auto-generated `id`, `created_at`, and `updated_at` timestamps.

<details>
<summary><strong>Go Deeper</strong></summary>

### Async variant

```python
from axonpush import AsyncAxonPush, EventType

async with AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.com") as client:
    event = await client.events.publish(
        "web_search",
        {"query": "AI agent frameworks"},
        channel_id=1,
        agent_id="researcher",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )
```

### All event types

The `EventType` enum covers the full agent lifecycle:

| Type | When to use |
|------|-------------|
| `AGENT_START` | Agent begins a run |
| `AGENT_END` | Agent completes a run |
| `AGENT_MESSAGE` | Agent produces a message |
| `AGENT_TOOL_CALL_START` | Agent invokes a tool |
| `AGENT_TOOL_CALL_END` | Tool returns a result |
| `AGENT_ERROR` | Something went wrong |
| `AGENT_HANDOFF` | Agent delegates to another agent |
| `AGENT_LLM_TOKEN` | Streaming token from the LLM |
| `CUSTOM` | Anything else (default) |

### Extra parameters

```python
event = client.events.publish(
    "web_search",
    {"query": "AI agents"},
    channel_id=1,
    agent_id="researcher",
    trace_id="tr_run_42",          # correlate events in a single run
    span_id="sp_abc123_0001",      # order events within a trace
    parent_event_id=previous.id,   # link to a parent event
    event_type=EventType.AGENT_TOOL_CALL_START,
    metadata={"model": "gpt-4", "latency_ms": 230},  # arbitrary context
)
```

</details>

## Next Steps

- [Add observability to your existing framework in 3 lines](02-framework-integrations.md)
- [Stream events live with SSE](03-live-dashboard-sse.md)
- [Trace a multi-step run end-to-end](04-distributed-tracing.md)
