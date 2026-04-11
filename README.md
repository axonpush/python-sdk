# axonpush

Python SDK for [AxonPush](https://axonpush.xyz) — real-time event infrastructure for AI agent systems.

Publish, subscribe, trace, and deliver agent events with sub-100ms latency. Drop-in integrations for LangChain, OpenAI Agents SDK, Claude/Anthropic, CrewAI, and the Python observability stack (stdlib `logging`, Loguru, structlog, OpenTelemetry).

## Install

```bash
pip install axonpush
```

With framework integrations:

```bash
pip install axonpush[langchain]       # LangChain/LangGraph
pip install axonpush[openai-agents]   # OpenAI Agents SDK
pip install axonpush[anthropic]       # Claude/Anthropic
pip install axonpush[crewai]          # CrewAI
pip install axonpush[deepagents]      # LangChain Deep Agents
```

With observability integrations:

```bash
pip install axonpush                  # stdlib logging — no extra deps
pip install axonpush[loguru]          # Loguru sink
pip install axonpush[structlog]       # structlog processor
pip install axonpush[otel]            # OpenTelemetry SpanExporter
pip install axonpush[all]             # Everything
```

## Quick Start

```python
from axonpush import AxonPush, EventType

with AxonPush(api_key="ak_...", tenant_id="1") as client:
    # Publish an event
    event = client.events.publish(
        "web_search",
        {"query": "AI agent frameworks"},
        channel_id=1,
        agent_id="researcher",
        trace_id="tr_run_42",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )

    # List events
    events = client.events.list(channel_id=1)

    # Get a trace summary
    summary = client.traces.get_summary("tr_run_42")
```

### Async

```python
from axonpush import AsyncAxonPush

async with AsyncAxonPush(api_key="ak_...", tenant_id="1") as client:
    event = await client.events.publish(
        "web_search",
        {"query": "AI agents"},
        channel_id=1,
        agent_id="researcher",
        event_type="agent.tool_call.start",
    )
```

## Framework Integrations

### LangChain / LangGraph

```python
from axonpush import AxonPush
from axonpush.integrations.langchain import AxonPushCallbackHandler

client = AxonPush(api_key="ak_...", tenant_id="1")
handler = AxonPushCallbackHandler(client, channel_id=1, agent_id="my-agent")

# All chain/tool/LLM events are published automatically
chain.invoke({"input": "..."}, config={"callbacks": [handler]})
```

### OpenAI Agents SDK

```python
from axonpush import AsyncAxonPush
from axonpush.integrations.openai_agents import AxonPushRunHooks

client = AsyncAxonPush(api_key="ak_...", tenant_id="1")
hooks = AxonPushRunHooks(client, channel_id=1)

result = await Runner.run(agent, input="...", hooks=hooks)
```

### Claude / Anthropic

```python
from axonpush import AxonPush
from axonpush.integrations.anthropic import AxonPushAnthropicTracer

client = AxonPush(api_key="ak_...", tenant_id="1")
tracer = AxonPushAnthropicTracer(client, channel_id=1)

# Wraps messages.create() — auto-emits events for tool_use, text, turns
response = tracer.create_message(
    anthropic_client,
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### CrewAI

```python
from axonpush import AxonPush
from axonpush.integrations.crewai import AxonPushCrewCallbacks

client = AxonPush(api_key="ak_...", tenant_id="1")
callbacks = AxonPushCrewCallbacks(client, channel_id=1)

callbacks.on_crew_start()
result = Crew(
    agents=[...],
    tasks=[...],
    step_callback=callbacks.on_step,
    task_callback=callbacks.on_task_complete,
).kickoff()
callbacks.on_crew_end(result)
```

## Logging & Observability

Ship logs and traces from your existing Python observability stack to AxonPush. All four integrations emit OpenTelemetry-shaped payloads, so the events line up with anything else you're already sending to an OTel-compatible backend.

> The stdlib `AxonPushLoggingHandler` installs a self-recursion filter by default that drops records from `httpx`, `httpcore`, and the SDK's own `axonpush` logger. Without it, each publish would trigger an `httpx` INFO log ("HTTP Request: POST /event 201 Created") that would get re-shipped, creating an infinite loop. The filter is always-on and cannot be disabled; you can add more excluded prefixes via `exclude_loggers=[...]`.

### Stdlib `logging` (FastAPI, Flask, Django, …)

```python
import logging
from axonpush import AxonPush
from axonpush.integrations.logging_handler import AxonPushLoggingHandler

client = AxonPush(api_key="ak_...", tenant_id="1")
handler = AxonPushLoggingHandler(client=client, channel_id=1, service_name="my-api")

logging.getLogger().addHandler(handler)
logging.info("order created", extra={"order_id": 1234})
```

**Django** uses `LOGGING` dictConfig, which can't pass a pre-built client — so the handler also accepts credential kwargs (or reads `AXONPUSH_API_KEY` / `AXONPUSH_TENANT_ID` from the environment):

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "axonpush": {
            "class": "axonpush.integrations.logging_handler.AxonPushLoggingHandler",
            "channel_id": 1,
            "service_name": "my-django-app",
            "exclude_loggers": ["django.db.backends"],  # optional
        },
    },
    "root": {"handlers": ["axonpush"], "level": "INFO"},
}
```

**FastAPI / Flask** — construct the handler with a pre-built `client=` in your app startup and attach it to `logging.getLogger()` (or `app.logger` for Flask).

> **Uvicorn propagation trap (FastAPI/Starlette):** uvicorn's default `LOGGING_CONFIG` sets `uvicorn.propagate=False`, so records emitted on `logging.getLogger("uvicorn.error")` **never reach the root logger**. If you only attach the handler to root, your app's startup/request logs will be invisible to AxonPush. Also attach the handler to `uvicorn.error` directly:
>
> ```python
> logging.getLogger().addHandler(axonpush_handler)
> logging.getLogger("uvicorn.error").addHandler(axonpush_handler)
> # Optional: one event per HTTP request
> # logging.getLogger("uvicorn.access").addHandler(axonpush_handler)
> ```

### Loguru

```python
from loguru import logger
from axonpush import AxonPush
from axonpush.integrations.loguru import create_axonpush_loguru_sink

client = AxonPush(api_key="ak_...", tenant_id="1")
sink = create_axonpush_loguru_sink(client=client, channel_id=1, service_name="my-api")
logger.add(sink, serialize=True)  # serialize=True is required

logger.error("connection refused", user_id=42)
```

### structlog

```python
import structlog
from axonpush import AxonPush
from axonpush.integrations.structlog import axonpush_structlog_processor

client = AxonPush(api_key="ak_...", tenant_id="1")
forwarder = axonpush_structlog_processor(client=client, channel_id=1, service_name="my-api")

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        forwarder,  # non-destructive — composes with other processors
        structlog.processors.JSONRenderer(),
    ],
)
structlog.get_logger().error("downstream timeout", endpoint="/search")
```

### Print capture (stdout/stderr → AxonPush)

For AI agents that emit free-form output via `print()`. Patches `sys.stdout` / `sys.stderr` with a tee stream that still writes to the original console.

```python
from axonpush import AxonPush
from axonpush.integrations.print_capture import setup_print_capture

client = AxonPush(api_key="ak_...", tenant_id="1")
handle = setup_print_capture(client, channel_id=1, agent_id="demo-agent")

print("agent starting")  # forwarded to AxonPush as an agent.log event
handle.unpatch()
```

### OpenTelemetry

If your service is already instrumented with the OTel SDK, add `AxonPushSpanExporter` to your tracer provider and every span ships to AxonPush alongside whatever other backends you export to.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from axonpush import AxonPush
from axonpush.integrations.otel import AxonPushSpanExporter

client = AxonPush(api_key="ak_...", tenant_id="1")
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(
        AxonPushSpanExporter(client=client, channel_id=1, service_name="my-api")
    )
)
trace.set_tracer_provider(provider)
```

## Real-Time Subscriptions

axonpush supports two real-time subscription mechanisms: **SSE** (Server-Sent Events) and **WebSocket** (Socket.IO).

### SSE (Server-Sent Events)

SSE is the simplest way to consume events in real time — no extra dependencies required.

#### Subscribe to all events on a channel

```python
from axonpush import AxonPush

with AxonPush(api_key="ak_...", tenant_id="1") as client:
    with client.channels.subscribe_sse(channel_id=1) as sub:
        for event in sub:
            print(event.agent_id, event.identifier, event.payload)
```

#### Subscribe to a specific event identifier

```python
with client.channels.subscribe_event_sse(channel_id=1, event_identifier="web_search") as sub:
    for event in sub:
        print(event.payload)
```

#### Filter by agent, event type, or trace

All SSE methods accept optional filters to narrow the event stream:

```python
with client.channels.subscribe_sse(
    channel_id=1,
    agent_id="researcher",
    event_type=EventType.AGENT_ERROR,
    trace_id="tr_run_42",
) as sub:
    for event in sub:
        print(f"[{event.agent_id}] {event.identifier}: {event.payload}")
```

### WebSocket (Socket.IO)

WebSocket subscriptions are callback-based and support bidirectional communication (subscribe, publish, unsubscribe).

```bash
pip install axonpush[websocket]
```

#### Sync

```python
ws = client.connect_websocket()
ws.on_event(lambda e: print(e.agent_id, e.payload))
ws.subscribe(channel_id=1, event_type="agent.tool_call.start")
ws.wait()  # blocks until disconnected
```

#### Async

```python
ws = await async_client.connect_websocket()
ws.on_event(lambda e: print(e.agent_id, e.payload))
await ws.subscribe(channel_id=1, event_type="agent.tool_call.start")
await ws.wait()
```

#### Publish and unsubscribe via WebSocket

```python
ws.publish(channel_id=1, identifier="status", payload={"step": "done"}, agent_id="worker")
ws.unsubscribe(channel_id=1)
ws.disconnect()
```

## Use Case Guides

Step-by-step guides for common scenarios:

- [See what your agent is doing — in real time](docs/use-cases/01-realtime-agent-events.md)
- [Add observability in 3 lines](docs/use-cases/02-framework-integrations.md)
- [Build a live dashboard with SSE](docs/use-cases/03-live-dashboard-sse.md)
- [Trace a multi-step agent run](docs/use-cases/04-distributed-tracing.md)
- [Get notified when your agent fails](docs/use-cases/05-error-webhooks.md)
- [Agent-to-agent communication](docs/use-cases/06-agent-to-agent-websockets.md)
- [Production error handling](docs/use-cases/07-production-error-handling.md)

## Resources

The client exposes Stripe-style resource objects:

| Resource | Methods |
|---|---|
| `client.events` | `publish()`, `list()` |
| `client.channels` | `create()`, `get()`, `update()`, `delete()`, `subscribe_sse()` |
| `client.apps` | `create()`, `get()`, `list()`, `update()`, `delete()` |
| `client.webhooks` | `create_endpoint()`, `list_endpoints()`, `delete_endpoint()`, `get_deliveries()` |
| `client.traces` | `list()`, `get_events()`, `get_summary()` |

## License

MIT
