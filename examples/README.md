# AxonPush Python SDK examples

Runnable recipes that demonstrate the AxonPush Python SDK at v0.0.10.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed
- A running AxonPush backend (default: `http://localhost:3000`)
- An API key and tenant (organisation) UUID

## Setup

```bash
cd examples
uv sync                       # core SDK only
uv sync --extra langchain     # + LangChain (07)
uv sync --extra deepagents    # + Deep Agents (09)
uv sync --extra loguru        # + Loguru (11)
uv sync --extra structlog     # + structlog (12)
uv sync --extra otel          # + OpenTelemetry (14)
```

Then set credentials in your shell or in `examples/.env`:

```bash
export AXONPUSH_API_KEY=ak_…
export AXONPUSH_TENANT_ID=…       # your org UUID
# optional
export AXONPUSH_BASE_URL=http://localhost:3000
export AXONPUSH_ENVIRONMENT=dev
export AXONPUSH_APP_ID=…          # reuse an existing app
export AXONPUSH_CHANNEL_ID=…      # reuse an existing channel
```

`AxonPush()` reads these env vars directly, so the examples never hard-code credentials. Each example will create a scratch app + channel when `AXONPUSH_APP_ID` / `AXONPUSH_CHANNEL_ID` are absent and clean them up on exit; supply your own UUIDs to keep the data around.

## Examples

| # | File | What it shows |
|---|------|---------------|
| 01 | `01_quickstart.py` | Create app + channel, publish three events, list, clean up. |
| 02 | `02_agent_tracing.py` | Multi-step agent trace: shared `trace_id`, span ids, `traces.summary()` at the end. |
| 03 | `03_realtime_mqtt.py` | Subscribe to a channel over MQTT-over-WSS via `client.connect_realtime()` while a publisher pumps events from another thread. |
| 04 | `04_multi_agent.py` | Planner → executor handoff. Both agents share one `trace_id` so the backend stitches the path together. |
| 05 | `05_webhooks.py` | Register a webhook endpoint with an `event_types=["agent.error"]` filter, publish matching + non-matching events, poll deliveries. Set `WEBHOOK_URL` to an [https://webhook.site/](https://webhook.site/) URL to actually receive them. |
| 06 | `06_async_client.py` | `AsyncAxonPush` + `asyncio.gather` — five "agents" publish concurrently. |
| 07 | `07_langchain.py` | `AxonPushCallbackHandler` for LangChain. Set `OPENAI_API_KEY` to actually run the chain. Needs `--extra langchain` plus `langchain-openai` in your shell. |
| 08 | `08_error_handling.py` | Walk through `AuthenticationError`, `NotFoundError`, `ValidationError`, the `RetryableError` mixin, plus the recommended catch-all order. |
| 09 | `09_deepagents.py` | `AxonPushDeepAgentHandler` for LangChain Deep Agents. Set `OPENAI_API_KEY` to run the agent. Needs `--extra deepagents`. |
| 10 | `10_stdlib_logging.py` | `AxonPushLoggingHandler` ships stdlib `logging` records as OTel-shaped `app.log` events. Includes a Django dictConfig snippet at the bottom. |
| 11 | `11_loguru.py` | `create_axonpush_loguru_sink` — Loguru sink with `serialize=True`. Needs `--extra loguru`. |
| 12 | `12_structlog.py` | `axonpush_structlog_processor` — non-destructive processor for structlog. Needs `--extra structlog`. |
| 13 | `13_print_capture.py` | `setup_print_capture` tees `sys.stdout` / `sys.stderr` into AxonPush as `agent.log` events. |
| 14 | `14_otel.py` | `AxonPushSpanExporter` plugged into a `TracerProvider`. Needs `--extra otel`. |

## Configuration

All examples import `examples/config.py`, which loads `.env` and exposes:

| Variable | Required | Default | Used by |
|----------|----------|---------|---------|
| `AXONPUSH_API_KEY` | Yes | — | All |
| `AXONPUSH_TENANT_ID` | Yes | — | All |
| `AXONPUSH_BASE_URL` | No | `http://localhost:3000` | All |
| `AXONPUSH_ENVIRONMENT` | No | — | All |
| `AXONPUSH_APP_ID` | No | scratch app | All |
| `AXONPUSH_CHANNEL_ID` | No | scratch channel | All |
| `OPENAI_API_KEY` | No | — | 07, 09 |
| `WEBHOOK_URL` | No | `https://httpbin.org/post` | 05 |
