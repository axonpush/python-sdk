# Build a Live Agent Dashboard with SSE

> Stream agent events to your terminal, Streamlit app, or web UI in real time. No polling, no WebSocket setup.

## The Problem

You can publish events. Now you want to watch them arrive as they happen. Maybe you're building a monitoring terminal, a Streamlit sidebar, or a React dashboard. Polling an API every second is wasteful and laggy. You need a persistent connection that pushes events to you.

## The Solution

```bash
pip install axonpush
```

```python
from axonpush import AxonPush

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    # Open a persistent SSE connection — events arrive as they happen
    with client.channels.subscribe_sse(channel_id=1) as stream:
        for event in stream:
            print(f"[{event.agent_id}] {event.identifier}: {event.payload}")
```

That's it. Every event published to channel 1 appears in your terminal the moment it's created.

### Filter the stream

```python
from axonpush import EventType

# Only errors from a specific agent
with client.channels.subscribe_sse(
    channel_id=1,
    agent_id="researcher",
    event_type=EventType.AGENT_ERROR,
) as stream:
    for event in stream:
        print(f"ERROR: {event.identifier} — {event.payload}")

# Only events with a specific name
with client.channels.subscribe_event_sse(
    channel_id=1,
    event_identifier="web_search",
) as stream:
    for event in stream:
        print(f"Search: {event.payload}")
```

## What Just Happened

- `subscribe_sse()` opens a Server-Sent Events connection to the channel. No extra dependencies needed.
- The `with` block manages the connection lifecycle — it closes cleanly when you break out of the loop or the block ends.
- Each iteration yields an `Event` object with `agent_id`, `identifier`, `payload`, `event_type`, and all other fields.
- Filters narrow the stream server-side. You can filter by `agent_id`, `event_type`, and `trace_id`.
- `subscribe_event_sse()` is a shortcut that filters by event `identifier` (e.g., only `"web_search"` events).

<details>
<summary><strong>Go Deeper</strong></summary>

### Combine publishing and subscribing

Run the subscriber in one process, the publisher in another:

**subscriber.py**
```python
from axonpush import AxonPush

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    with client.channels.subscribe_sse(channel_id=1) as stream:
        for event in stream:
            print(f"[{event.agent_id}] {event.identifier}: {event.payload}")
```

**publisher.py**
```python
from axonpush import AxonPush, EventType

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    client.events.publish(
        "web_search",
        {"query": "AI agents", "results": 12},
        channel_id=1,
        agent_id="researcher",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )
```

Run `python subscriber.py` in one terminal, then `python publisher.py` in another. The subscriber prints the event instantly.

### SSE with framework integrations

Publish with a LangChain callback handler, subscribe with SSE in another process:

```python
# Process 1: LangChain agent publishes events automatically
from axonpush.integrations.langchain import AxonPushCallbackHandler
handler = AxonPushCallbackHandler(client, channel_id=1, agent_id="langchain-agent")
chain.invoke({"input": "..."}, config={"callbacks": [handler]})

# Process 2: SSE subscriber sees all chain/tool/LLM events in real time
with client.channels.subscribe_sse(channel_id=1) as stream:
    for event in stream:
        print(event.identifier, event.payload)
```

### Using SSE in a background thread

```python
import threading

received = []

def listen():
    with client.channels.subscribe_sse(channel_id=1) as stream:
        for event in stream:
            received.append(event)
            if len(received) >= 10:
                break

thread = threading.Thread(target=listen, daemon=True)
thread.start()

# Your agent does its work here...
client.events.publish("action", {"step": 1}, channel_id=1, agent_id="worker")

thread.join(timeout=10)
print(f"Received {len(received)} events")
```

### All SSE filter parameters

| Parameter | Type | Effect |
|-----------|------|--------|
| `agent_id` | `str` | Only events from this agent |
| `event_type` | `EventType` or `str` | Only events of this type |
| `trace_id` | `str` | Only events in this trace |

Filters stack — pass multiple to narrow further.

</details>

## Next Steps

- [Trace a multi-step run end-to-end](04-distributed-tracing.md)
- [Get notified when your agent fails (webhooks)](05-error-webhooks.md)
- [Bidirectional real-time with WebSockets](06-agent-to-agent-websockets.md)
