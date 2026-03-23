# Build Agent-to-Agent Communication with WebSockets

> Bidirectional, low-latency pub/sub between agents. One agent publishes, another reacts instantly.

## The Problem

You have multiple agents that need to coordinate. Agent A discovers something. Agent B needs to react immediately. HTTP polling wastes resources and adds latency. SSE streams are one-directional — you can listen, but you can't publish back over the same connection. You need bidirectional, real-time communication.

## The Solution

```bash
pip install axonpush[websocket]
```

```python
from axonpush import AxonPush, EventType

client = AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.com")

# Agent B: subscribe and react
ws = client.connect_websocket()
ws.on_event(lambda e: print(f"[{e.agent_id}] {e.identifier}: {e.payload}"))
ws.subscribe(channel_id=1)

# Agent A: publish a discovery
ws.publish(
    channel_id=1,
    identifier="research_complete",
    payload={"topic": "AI frameworks", "sources": 12},
    agent_id="researcher",
    event_type=EventType.AGENT_END,
)

# Block until done
ws.wait()
```

## What Just Happened

- `connect_websocket()` opens a Socket.IO connection to AxonPush. It handles authentication automatically.
- `on_event()` registers a callback that fires for every event matching your subscriptions.
- `subscribe(channel_id=1)` tells the server to push channel 1 events to this connection.
- `publish()` sends an event over the same WebSocket — no separate HTTP call needed.
- `wait()` blocks the main thread until the connection is closed. Useful for long-running agent processes.
- Both subscribe and publish happen over a single persistent connection.

<details>
<summary><strong>Go Deeper</strong></summary>

### Two-agent coordination pattern

```python
import threading
from axonpush import AxonPush, EventType

client = AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.com")

# Agent B: the reactor
def agent_b():
    ws = client.connect_websocket()

    def handle(event):
        if event.identifier == "research_complete":
            print(f"Agent B: writing report based on {event.payload['sources']} sources")
            ws.publish(
                channel_id=1,
                identifier="report_written",
                payload={"pages": 3},
                agent_id="writer",
                event_type=EventType.AGENT_END,
            )
            ws.disconnect()

    ws.on_event(handle)
    ws.subscribe(channel_id=1, agent_id="researcher")  # only researcher events
    ws.wait()

thread = threading.Thread(target=agent_b, daemon=True)
thread.start()

# Agent A: the researcher
ws_a = client.connect_websocket()
ws_a.publish(
    channel_id=1,
    identifier="research_complete",
    payload={"topic": "AI frameworks", "sources": 12},
    agent_id="researcher",
)
ws_a.disconnect()

thread.join(timeout=10)
```

### Filtered subscriptions

```python
ws = client.connect_websocket()

# Only tool call events from a specific agent in a specific trace
ws.subscribe(
    channel_id=1,
    agent_id="researcher",
    event_type=EventType.AGENT_TOOL_CALL_START,
    trace_id="tr_run_42",
)
```

| Filter | Type | Effect |
|--------|------|--------|
| `agent_id` | `str` | Only events from this agent |
| `event_type` | `EventType` or `str` | Only events of this type |
| `trace_id` | `str` | Only events in this trace |

### Unsubscribe and disconnect

```python
ws.unsubscribe(channel_id=1)   # stop receiving events from channel 1
ws.disconnect()                 # close the WebSocket connection
```

### Async WebSocket

```python
from axonpush import AsyncAxonPush

async with AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.com") as client:
    ws = await client.connect_websocket()
    ws.on_event(lambda e: print(e.identifier, e.payload))
    await ws.subscribe(channel_id=1)

    await ws.publish(
        channel_id=1,
        identifier="discovery",
        payload={"data": "..."},
        agent_id="researcher",
    )

    await ws.wait()
```

### Architecture pattern: channel-per-team

Use separate channels to isolate agent communication:

```python
# Research team communicates on channel 1
ws.subscribe(channel_id=1)

# Writing team communicates on channel 2
ws.subscribe(channel_id=2)

# Cross-team coordination happens on channel 3
ws.subscribe(channel_id=3)
```

This prevents noisy agents from flooding other teams' event streams.

</details>

## Next Steps

- [Handle errors and rate limits in production](07-production-error-handling.md)
- [Get notified on failures with webhooks](05-error-webhooks.md)
- [Trace agent coordination end-to-end](04-distributed-tracing.md)
