# AxonPush Python SDK Examples

Runnable recipes that demonstrate the AxonPush Python SDK.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed
- A running AxonPush server (default: `http://localhost:3000`)
- An API key and tenant (organization) ID

## Setup

```bash
cd examples
cp .env.example .env   # then edit .env with your credentials
uv sync
```

For the LangChain example:

```bash
uv sync --extra langchain
```

## Running

```bash
uv run 01_quickstart.py
uv run 02_agent_tracing.py
uv run 03_realtime_sse.py
# ... etc
```

## Examples

| # | File | Description |
|---|------|-------------|
| 01 | `01_quickstart.py` | Create app, channel, publish events, list them |
| 02 | `02_agent_tracing.py` | Multi-step agent trace with spans and summary |
| 03 | `03_realtime_sse.py` | Subscribe to live events via SSE |
| 04 | `04_multi_agent.py` | Two-agent handoff with full trace |
| 05 | `05_webhooks.py` | Set up webhook endpoint and check deliveries |
| 06 | `06_async_client.py` | Async client with concurrent publishing |
| 07 | `07_langchain.py` | LangChain callback handler integration |
| 08 | `08_error_handling.py` | Graceful error handling patterns |

## Configuration

All examples read from `config.py`, which loads `.env` automatically. Available variables:

| Variable | Required | Default |
|----------|----------|---------|
| `AXONPUSH_API_KEY` | Yes | — |
| `AXONPUSH_TENANT_ID` | Yes | — |
| `AXONPUSH_BASE_URL` | No | `http://localhost:3000` |
| `OPENAI_API_KEY` | No | — (for 07_langchain.py) |
| `WEBHOOK_URL` | No | `https://httpbin.org/post` |
