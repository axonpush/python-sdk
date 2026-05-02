# axonpush

[![PyPI](https://img.shields.io/pypi/v/axonpush.svg)](https://pypi.org/project/axonpush/)

Python SDK for [AxonPush](https://axonpush.xyz) — real-time event infrastructure for AI agent systems.

Publish, subscribe, trace, and deliver agent events with sub-100ms latency. Drop-in integrations for LangChain, LangGraph Deep Agents, OpenAI Agents SDK, Anthropic, CrewAI, and the Python observability stack (stdlib `logging`, Loguru, structlog, OpenTelemetry, Sentry).

> **v0.0.10 is a breaking release.** All IDs are now `str` UUIDs (was `int` / `Union[int, str]`); the deprecated `connect_websocket` alias has been removed; models live under a flat `axonpush.models` namespace. See [`CHANGELOG.md`](CHANGELOG.md) for the migration guide.

## Install

```bash
pip install axonpush                  # or: uv add axonpush
pip install axonpush[langchain]       # LangChain / LangGraph
pip install axonpush[deepagents]      # LangChain Deep Agents
pip install axonpush[openai-agents]   # OpenAI Agents SDK
pip install axonpush[anthropic]       # Anthropic
pip install axonpush[crewai]          # CrewAI
pip install axonpush[loguru]          # Loguru sink
pip install axonpush[structlog]       # structlog processor
pip install axonpush[otel]            # OpenTelemetry SpanExporter
pip install axonpush[rq]              # Redis Queue durable backend
pip install axonpush[all]             # everything above
```

`paho-mqtt` (sync) and `aiomqtt` (async) are core dependencies — realtime works out of the box.

## Quick start

```python
from axonpush import AxonPush, EventType

# Reads AXONPUSH_API_KEY / AXONPUSH_TENANT_ID / AXONPUSH_BASE_URL from env
# when the kwargs are omitted.
with AxonPush() as client:
    event = client.events.publish(
        "web_search",
        {"query": "AI agent frameworks"},
        channel_id="…channel uuid…",
        agent_id="researcher",
        event_type=EventType.AGENT_TOOL_CALL_START,
    )
    # event.event_id is server-assigned; event.queued is True within ~1 ms.

    listing = client.events.list(channel_id="…channel uuid…", limit=20)
    for ev in listing.data:
        print(ev.event_type, ev.identifier)
```

### Async

```python
import asyncio
from axonpush import AsyncAxonPush

async def main():
    async with AsyncAxonPush() as client:
        await client.events.publish(
            "web_search",
            {"query": "AI agents"},
            channel_id="…channel uuid…",
            agent_id="researcher",
            event_type="agent.tool_call.start",
        )

asyncio.run(main())
```

## Configuration

Every kwarg falls back to an `AXONPUSH_…` env var; constructor kwargs win.

```python
AxonPush(
    api_key="ak_…",        # AXONPUSH_API_KEY
    tenant_id="…",         # AXONPUSH_TENANT_ID
    base_url="https://api.axonpush.xyz",  # AXONPUSH_BASE_URL
    environment="prod",    # AXONPUSH_ENVIRONMENT
    timeout=30.0,          # AXONPUSH_TIMEOUT
    max_retries=3,         # AXONPUSH_MAX_RETRIES
    fail_open=False,       # AXONPUSH_FAIL_OPEN
)
```

`fail_open=True` swallows `APIConnectionError` and returns `None` from every resource call — useful when AxonPush observability must never break the host application.

## Realtime (MQTT-over-WSS)

`client.connect_realtime()` returns a `RealtimeClient` (sync) or `AsyncRealtimeClient` (async) connected to AWS IoT Core. Credentials are fetched via `/auth/iot-credentials` and rotated automatically before they expire.

```python
rt = client.connect_realtime(environment="prod")
rt.subscribe(
    channel_id="…channel uuid…",
    app_id="…app uuid…",
    callback=lambda msg: print(msg["eventType"], msg["payload"]),
)
# … publishes happen elsewhere …
rt.disconnect()
```

Topics are `axonpush/{org}/{env}/{app}/{channel}/{event_type}/{agent}`. Omitted slots become MQTT `+` wildcards on subscribe and `default` (env) / `_` (agent) on publish.

## Resources

The client exposes Stripe-style resource accessors:

| Accessor | Methods |
|---|---|
| `client.events` | `publish`, `list`, `search` |
| `client.channels` | `create`, `get`, `update`, `delete` |
| `client.apps` | `list`, `get`, `create`, `update`, `delete` |
| `client.environments` | `list`, `create`, `update`, `delete`, `promote_to_default` |
| `client.webhooks` | `create_endpoint`, `list_endpoints`, `delete_endpoint`, `deliveries` |
| `client.traces` | `list`, `summary`, `events`, `stats` |
| `client.api_keys` | `list`, `create`, `delete` |
| `client.organizations` | `list`, `get`, `create`, `update`, `delete`, `invite`, `remove_member`, `transfer_ownership` |

`events.list()` and `events.search()` return an `EventListResponseDto` with `.data` (list) and `.meta` (cursor + count).

## Errors

```python
from axonpush import (
    AxonPushError,            # base
    APIConnectionError,       # network / DNS / read timeout
    AuthenticationError,      # 401
    ForbiddenError,           # 403
    NotFoundError,            # 404
    ValidationError,          # 422 / code='validation_error'
    RateLimitError,           # 429 — carries .retry_after
    ServerError,              # 5xx
    RetryableError,           # mixin: APIConnectionError, RateLimitError, ServerError
)
```

Every exception carries `request_id`, `status_code`, `code`, `hint` parsed from the backend's `{ code, message, hint, requestId }` envelope. Anything that subclasses `RetryableError` is safe to retry; the SDK's transport already retries them up to `max_retries` with exponential backoff.

## Integrations

| Library | Module | Class / function |
|---|---|---|
| LangChain | `axonpush.integrations.langchain` | `AxonPushCallbackHandler`, `AsyncAxonPushCallbackHandler` |
| LangGraph Deep Agents | `axonpush.integrations.deepagents` | `AxonPushDeepAgentHandler`, `AsyncAxonPushDeepAgentHandler` |
| OpenAI Agents SDK | `axonpush.integrations.openai_agents` | `AxonPushRunHooks` |
| Anthropic | `axonpush.integrations.anthropic` | `AxonPushAnthropicTracer` |
| CrewAI | `axonpush.integrations.crewai` | `AxonPushCrewCallbacks` |
| stdlib `logging` | `axonpush.integrations.logging_handler` | `AxonPushLoggingHandler` |
| Loguru | `axonpush.integrations.loguru` | `create_axonpush_loguru_sink` |
| structlog | `axonpush.integrations.structlog` | `axonpush_structlog_processor` |
| `print()` capture | `axonpush.integrations.print_capture` | `setup_print_capture` |
| OpenTelemetry | `axonpush.integrations.otel` | `AxonPushSpanExporter` |
| Sentry compat | `axonpush.integrations.sentry` | `install_sentry` |

All log/span integrations emit OpenTelemetry-shaped payloads (`severityNumber`, `severityText`, `body`, `attributes`, `resource`) so events line up with anything else you ship to an OTel-compatible backend.

### Publishing modes

Every integration accepts a `mode` parameter:

| Mode | Backend | Use case |
|---|---|---|
| `"background"` (default) | In-process bounded queue | Most apps |
| `"sync"` | Direct HTTP call | Tests, debugging |
| `"rq"` | [python-rq](https://python-rq.org/) | Durable delivery, serverless, high volume |

```python
from redis import Redis
from axonpush.integrations.langchain import AxonPushCallbackHandler

handler = AxonPushCallbackHandler(
    client, channel_id="…",
    mode="rq",
    rq_options={"redis_conn": Redis(), "queue_name": "axonpush"},
)
```

Then run `rq worker axonpush` somewhere.

## Tracing

Group related events with a shared `trace_id`. The SDK auto-creates one per call, but you'll usually want to pin a trace to a logical request:

```python
from axonpush import get_or_create_trace

trace = get_or_create_trace()
client.events.publish(
    "step.start", {"step": 1},
    channel_id="…",
    trace_id=trace.trace_id,
    span_id=trace.next_span_id(),
)

summary = client.traces.summary(trace.trace_id)
print(summary.event_count, summary.duration, summary.tool_call_count)
```

`get_or_create_trace()` reads the active context (set via `with TraceContext(...):`) when one exists, so framework integrations propagate the trace automatically.

## Examples

`examples/` contains 14 runnable recipes — quickstart, tracing, MQTT, webhooks, async, error handling, plus one example per integration. Each reads `AXONPUSH_API_KEY` / `AXONPUSH_TENANT_ID` from your environment. See [`examples/README.md`](examples/README.md) for the full table.

## Advanced

For internal contracts, the resource ownership matrix, the OpenAPI codegen layer, and exception handling internals, see [`SHARED-CONTRACT.md`](SHARED-CONTRACT.md).

## License

MIT
