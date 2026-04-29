# axonpush

Python SDK for [AxonPush](https://axonpush.xyz) — real-time event infrastructure for AI agent systems.

Publish, subscribe, trace, and deliver agent events with sub-100ms latency. Drop-in integrations for LangChain, OpenAI Agents SDK, Claude/Anthropic, CrewAI, Deep Agents, and the Python observability stack (stdlib `logging`, Loguru, structlog, OpenTelemetry, Sentry).

> **v0.1.0 is a breaking release.** Realtime moves from Socket.IO to AWS IoT Core MQTT-over-WSS, SSE is gone, and `events.search(q="...")` (Lucene) is replaced with typed query parameters. See the [Migration guide](#migrating-from-00x) at the bottom.

## Install

```bash
pip install axonpush   # or: uv add axonpush
```

`paho-mqtt` (sync) and `aiomqtt` (async) are core dependencies — realtime works out of the box, no extra installs.

With framework integrations:

```bash
pip install axonpush[langchain]       # LangChain/LangGraph
pip install axonpush[openai-agents]   # OpenAI Agents SDK
pip install axonpush[anthropic]       # Claude/Anthropic
pip install axonpush[crewai]          # CrewAI
pip install axonpush[deepagents]      # LangChain Deep Agents
pip install axonpush[rq]              # Redis Queue backend (python-rq)
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

### Sync

```python
from axonpush import AxonPush, EventType

with AxonPush(api_key="ak_...", tenant_id="org_...", environment="production") as client:
    # Publish an event over REST
    event = client.events.publish(
        "web_search",
        {"query": "AI agent frameworks"},
        channel_id="ch_main",
        agent_id="researcher",
        trace_id="tr_run_42",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )
    # event.queued == True, event.id is None — publishes are async-ingested
    # by default. See "Response shape" below.

    # Subscribe in real time over MQTT-over-WSS
    rt = client.connect_realtime()
    rt.on_event(lambda e: print(e.agent_id, e.identifier, e.payload))
    rt.subscribe(channel_id="ch_main", event_type="agent.tool_call.start")
    rt.wait()  # blocks until rt.disconnect() is called from another thread
```

### Async

```python
import asyncio
from axonpush import AsyncAxonPush

async def main():
    async with AsyncAxonPush(api_key="ak_...", tenant_id="org_...") as client:
        await client.events.publish(
            "web_search",
            {"query": "AI agents"},
            channel_id="ch_main",
            agent_id="researcher",
            event_type="agent.tool_call.start",
        )

        rt = await client.connect_realtime()
        rt.on_event(lambda e: print(e.agent_id, e.payload))
        await rt.subscribe(channel_id="ch_main", event_type="agent.error")
        await rt.wait()

asyncio.run(main())
```

### Response shape

By default, `events.publish()` returns as soon as the server has queued the event — typically under 1&nbsp;ms. The returned `Event` carries `identifier`, `queued=True`, `created_at`, and the resolved `environment_id`, but **not** a DB-assigned `id` (`event.id` is `None`). Treat `event.identifier` and `event.trace_id` as the durable correlation keys. List endpoints and MQTT subscriptions return the fully-persisted shape (with `id`) once the event is written.

## Configuration

```python
AxonPush(
    api_key="ak_...",
    tenant_id="org_...",
    base_url="https://api.axonpush.xyz",   # optional — selfhost / staging
    iot_endpoint=None,                     # optional — pre-pin AWS IoT ATS endpoint
    environment="production",              # optional — auto-detected from env vars
    timeout=30.0,
    fail_open=True,
)
```

`AsyncAxonPush(...)` takes the identical kwargs.

`iot_endpoint` is the AWS IoT Core ATS endpoint (e.g. `xyz-ats.iot.us-east-1.amazonaws.com`). If you omit it, the SDK auto-discovers it from `GET /auth/iot-credentials` on first realtime connect — most callers should leave this `None`.

## Publishing events (REST)

```python
client.events.publish(
    identifier="web_search",
    payload={"query": "...", "max_results": 10},
    channel_id="ch_main",
    agent_id="researcher",          # optional
    trace_id="tr_run_42",           # auto-generated if omitted
    event_type=EventType.AGENT_TOOL_CALL_START,  # str also accepted
    metadata={"region": "us-east-1"},
)
```

`identifier` is your free-form correlation key. `event_type` is one of the `EventType` enum values (or any string the backend recognises). Omitting `trace_id` ties the event to the ambient trace if one is active, or starts a new one.

## Subscribing in real time (MQTT)

`client.connect_realtime()` returns a `RealtimeClient` (sync) or `AsyncRealtimeClient` (async) connected to AWS IoT Core via MQTT-over-WSS. Credentials are fetched from `/auth/iot-credentials` and refreshed automatically before they expire (with ~60&nbsp;s lead time).

`client.connect_websocket()` is preserved as an alias of `connect_realtime()`, and `WebSocketClient` aliases `RealtimeClient` — existing 0.0.x callers keep working without code changes.

### Sync

```python
rt = client.connect_realtime()
rt.on_event(lambda e: print(e.agent_id, e.payload))
rt.subscribe(channel_id="ch_main", event_type="agent.error")
rt.publish(
    channel_id="ch_main",
    identifier="status",
    payload={"step": "done"},
    agent_id="worker",
)
rt.wait()         # blocks until disconnect()
rt.disconnect()
```

### Async

```python
rt = await async_client.connect_realtime()
rt.on_event(lambda e: print(e.agent_id, e.payload))           # sync or async callback
await rt.subscribe(channel_id="ch_main", agent_id="researcher")
await rt.publish(
    channel_id="ch_main",
    identifier="status",
    payload={"step": "done"},
    agent_id="worker",
)
await rt.wait()
await rt.disconnect()
```

### Topics and wildcards

Topics are structured as `axonpush/{org}/{app}/{channel}/{event_type}/{agent_id}`. Each `subscribe()` argument maps to one slot of the topic; omitted arguments become MQTT `+` single-level wildcards.

| Call | Resulting topic |
|---|---|
| `subscribe("ch_main")` | `axonpush/org_…/+/ch_main/+/+` (all events on the channel) |
| `subscribe("ch_main", event_type="agent.error")` | `axonpush/org_…/+/ch_main/agent.error/+` |
| `subscribe("ch_main", agent_id="researcher")` | `axonpush/org_…/+/ch_main/+/researcher` |
| `subscribe("ch_main", event_type="agent.error", agent_id="researcher")` | `axonpush/org_…/+/ch_main/agent.error/researcher` |

If you need to build topics yourself (e.g. for cross-language tooling) the helpers are public:

```python
from axonpush.realtime.topics import build_subscribe_topic, build_publish_topic
```

### Error handling and reconnects

`paho-mqtt` (sync) and `aiomqtt` (async) handle TCP-level reconnects. The SDK additionally re-issues `SUBSCRIBE` for every active filter on each reconnect and rotates IoT credentials before they expire — long-running subscribers don't need a watchdog. Connection failures during `connect_realtime()` are suppressed when `fail_open=True` (the default) and surface as a `None` return value plus a warning log; pass `fail_open=False` to raise instead.

## Searching events (REST)

`events.list()` and `events.search()` take typed kwargs that map to the backend's typed query schema — no Lucene. The server picks the optimal access pattern based on which fields are present.

```python
from datetime import datetime, timedelta, timezone

events = client.events.list(
    channel_id="ch_main",
    event_type=["agent.tool_call.start", "agent.tool_call.end"],
    agent_id="researcher",
    trace_id="tr_run_42",
    since=datetime.now(timezone.utc) - timedelta(hours=1),
    until=datetime.now(timezone.utc),
    limit=100,
    cursor=None,
)
```

`payload_filter` accepts a [sift.js](https://github.com/crcn/sift.js)-compatible MongoDB-style operator dict, JSON-encoded over the wire and applied server-side:

```python
events = client.events.list(
    channel_id="ch_main",
    payload_filter={
        "user.id": {"$eq": "u_123"},
        "duration_ms": {"$gt": 1000},
        "status": {"$in": ["error", "timeout"]},
    },
)
```

Use `events.search()` (same kwargs, plus optional `app_id` / `environment_id`) to query across channels.

## Framework integrations

Every integration emits OpenTelemetry-shaped payloads, so events line up with anything else you ship to an OTel-compatible backend.

### LangChain / LangGraph

```python
from axonpush.integrations.langchain import AxonPushCallbackHandler

handler = AxonPushCallbackHandler(client, channel_id="ch_main", agent_id="my-agent")
chain.invoke({"input": "..."}, config={"callbacks": [handler]})
```

For async graphs use `axonpush.integrations.langchain.get_langchain_handler(async_client, ...)`.

### OpenAI Agents SDK

```python
from axonpush.integrations.openai_agents import AxonPushRunHooks

hooks = AxonPushRunHooks(async_client, channel_id="ch_main")
result = await Runner.run(agent, input="...", hooks=hooks)
await hooks.flush()  # optional — drain pending publishes before exit
```

### Claude / Anthropic

```python
from axonpush.integrations.anthropic import AxonPushAnthropicTracer

tracer = AxonPushAnthropicTracer(client, channel_id="ch_main")
response = tracer.create_message(
    anthropic_client,
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### CrewAI

```python
from axonpush.integrations.crewai import AxonPushCrewCallbacks

callbacks = AxonPushCrewCallbacks(client, channel_id="ch_main")
callbacks.on_crew_start()
result = Crew(
    agents=[...], tasks=[...],
    step_callback=callbacks.on_step,
    task_callback=callbacks.on_task_complete,
).kickoff()
callbacks.on_crew_end(result)
```

### Deep Agents

```python
from axonpush.integrations.deepagents import AxonPushDeepAgentsTracer
tracer = AxonPushDeepAgentsTracer(client, channel_id="ch_main")
```

### Loguru

```python
from loguru import logger
from axonpush.integrations.loguru import create_axonpush_loguru_sink

sink = create_axonpush_loguru_sink(client=client, channel_id="ch_main", service_name="my-api")
logger.add(sink, serialize=True)  # serialize=True is required
```

### structlog

```python
import structlog
from axonpush.integrations.structlog import axonpush_structlog_processor

forwarder = axonpush_structlog_processor(client=client, channel_id="ch_main", service_name="my-api")
structlog.configure(processors=[
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
    forwarder,
    structlog.processors.JSONRenderer(),
])
```

### Stdlib `logging` (FastAPI, Flask, Django, …)

```python
import logging
from axonpush.integrations.logging_handler import AxonPushLoggingHandler

handler = AxonPushLoggingHandler(client=client, channel_id="ch_main", service_name="my-api")
logging.getLogger().addHandler(handler)
logging.info("order created", extra={"order_id": 1234})
```

A self-recursion filter drops records from `httpx`, `httpcore`, and `axonpush` so a publish doesn't loop back through the handler. Add more excluded prefixes via `exclude_loggers=[...]`.

> **Uvicorn propagation trap (FastAPI/Starlette):** uvicorn's default `LOGGING_CONFIG` sets `uvicorn.propagate=False`, so records emitted on `logging.getLogger("uvicorn.error")` never reach the root logger. Also attach the handler to `uvicorn.error` directly: `logging.getLogger("uvicorn.error").addHandler(axonpush_handler)`.

### AWS Lambda / Google Cloud Functions / Azure Functions

Serverless containers are frozen between invocations, so the background worker thread can't drain the queue during the freeze. Wrap your handler with `@flush_after_invocation`:

```python
import os, logging
from axonpush import AxonPush
from axonpush.integrations.logging_handler import (
    AxonPushLoggingHandler,
    flush_after_invocation,
)

client = AxonPush(
    api_key=os.environ["AXONPUSH_API_KEY"],
    tenant_id=os.environ["AXONPUSH_TENANT_ID"],
)
handler = AxonPushLoggingHandler(client=client, channel_id="ch_main", service_name="my-lambda")
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

@flush_after_invocation(handler)
def lambda_handler(event, context):
    logging.info("processing event", extra={"event_id": event["id"]})
    return {"statusCode": 200}
```

Pass multiple handlers to flush them in one wrap: `@flush_after_invocation(logging_handler, otel_exporter, structlog_processor)`.

### OpenTelemetry

If your service is already instrumented with the OTel SDK, add `AxonPushSpanExporter` to your tracer provider — every span is `POST`ed to `/event` alongside whatever other backends you export to.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from axonpush.integrations.otel import AxonPushSpanExporter

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(
        AxonPushSpanExporter(client=client, channel_id="ch_main", service_name="my-api")
    )
)
trace.set_tracer_provider(provider)
```

### Sentry

If your app is already using `sentry-sdk`, point it at AxonPush with a one-liner. `install_sentry()` builds a Sentry-format DSN from your AxonPush credentials and calls `sentry_sdk.init(**kwargs)` — captured errors from Sentry's Flask/FastAPI/Django/Celery instrumentations flow into your AxonPush channel instead of Sentry's cloud.

```bash
pip install sentry-sdk   # axonpush does not bundle sentry-sdk
```

```python
from axonpush import install_sentry

install_sentry(
    api_key="ak_...",
    channel_id=42,
    environment="production",
    release="my-app@1.2.3",
    traces_sample_rate=0.1,
    send_default_pii=False,
)
```

`api_key`, `channel_id`, and `host` fall back to `AXONPUSH_API_KEY`, `AXONPUSH_CHANNEL_ID`, and `AXONPUSH_HOST` (default `api.axonpush.xyz`) if omitted. `environment` uses the same auto-detect precedence as the client (`AXONPUSH_ENVIRONMENT` → `SENTRY_ENVIRONMENT` → `APP_ENV` → `ENV`). Pass `dsn="..."` if you need a fully-formed DSN instead.

## Publishing modes

All integrations accept a `mode` parameter to control how events reach AxonPush:

| Mode | Backend | Best for |
|------|---------|----------|
| `"background"` (default) | In-process queue (sync) or `asyncio.create_task` (async) | Most apps — zero config |
| `"rq"` | Redis Queue ([python-rq](https://python-rq.org/)) | Durable delivery, serverless, high volume |
| `"sync"` | Direct HTTP call | Debugging, tests |

```python
from redis import Redis
from axonpush.integrations.langchain import AxonPushCallbackHandler

handler = AxonPushCallbackHandler(
    client, channel_id="ch_main",
    mode="rq",
    rq_options={"redis_conn": Redis(), "queue_name": "axonpush"},
)
```

```bash
rq worker axonpush
```

## Environments

Tag every event with the environment it came from (`"production"`, `"staging"`, `"eval"`, …). AxonPush uses the tag server-side for isolation, filtering, and per-env quotas. The SDK forwards it as an `X-Axonpush-Environment` header on every request and threads it into the logging handler's OTel resource attributes.

```python
client = AxonPush(api_key="ak_...", tenant_id="org_...", environment="production")

# Per-call override:
client.events.publish("rerun_eval", {"dataset": "v2"}, channel_id="ch_main", environment="eval")

# Temporary override with a context manager:
with client.environment("eval"):
    for row in dataset:
        client.events.publish("row_processed", {"id": row.id}, channel_id="ch_main")
```

If you omit `environment=`, the SDK auto-detects it from the first of these that's set: **`AXONPUSH_ENVIRONMENT`** → `SENTRY_ENVIRONMENT` → `APP_ENV` → `ENV`.

## Resources

The client exposes Stripe-style resource objects:

| Resource | Methods |
|---|---|
| `client.events` | `publish()`, `list()`, `search()` |
| `client.channels` | `create()`, `get()`, `update()`, `delete()` |
| `client.apps` | `create()`, `get()`, `list()`, `update()`, `delete()` |
| `client.webhooks` | `create_endpoint()`, `list_endpoints()`, `delete_endpoint()`, `get_deliveries()` |
| `client.traces` | `list()`, `get_events()`, `get_summary()` |

## Migrating from 0.0.x

### Realtime: Socket.IO → MQTT-over-WSS

Existing call sites keep working:

```python
ws = client.connect_websocket()                    # alias of connect_realtime()
ws.on_event(lambda e: print(e.payload))
ws.subscribe(channel_id="ch_main", event_type="agent.error")
ws.wait()
```

Under the hood this is now `RealtimeClient` (MQTT-over-WSS to AWS IoT Core) instead of a Socket.IO client. The public surface — `connect`, `on_event`, `subscribe(channel, event_type=None, agent_id=None)`, `publish`, `wait`, `disconnect` — is preserved. The `WebSocketClient` name is aliased to `RealtimeClient`. Drop the `[websocket]` extra from your install — Socket.IO is no longer a dependency, and `paho-mqtt` / `aiomqtt` are core.

If you were importing the Socket.IO `/events` namespace directly, that's gone. Use `connect_realtime()` instead.

### SSE → MQTT

`channels.subscribe_sse()` and `channels.subscribe_event_sse()` are retained as deprecation shims that internally open an MQTT subscription and emit a `DeprecationWarning` on first call. They will be removed in v0.2.0. Replace:

```python
# Before (0.0.x):
with client.channels.subscribe_sse(channel_id=1, event_type="agent.error") as sub:
    for event in sub:
        print(event.payload)

# After (0.1.0):
rt = client.connect_realtime()
rt.on_event(lambda e: print(e.payload))
rt.subscribe(channel_id=1, event_type="agent.error")
rt.wait()
```

### Event search: Lucene → typed kwargs

The `q="..."` Lucene parameter on `events.list()` / `events.search()` is removed. Translate Lucene queries into typed kwargs and a `payload_filter` dict:

```python
# Before (0.0.x):
events = client.events.search(q='channelId:1 AND eventType:agent.error AND payload.user_id:u_123')

# After (0.1.0):
events = client.events.list(
    channel_id="1",
    event_type="agent.error",
    payload_filter={"user_id": {"$eq": "u_123"}},
)
```

`payload_filter` accepts the full sift.js operator vocabulary (`$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$exists`, `$regex`, `$and`, `$or`, …) and is JSON-encoded over the wire.

## License

MIT
