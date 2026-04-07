# AxonPush Use Case Guides

Scenario-driven guides for building with AxonPush. Each takes under 2 minutes to read and includes copy-pasteable code.

## Prerequisites

```bash
pip install axonpush
```

You need an AxonPush API key and tenant ID. Get them from the [AxonPush dashboard](https://axonpush.xyz).

## Guides

| # | Guide | Difficulty | What you'll learn |
|---|-------|------------|-------------------|
| 1 | [See what your agent is doing — in real time](01-realtime-agent-events.md) | Beginner | Publish and retrieve agent events |
| 2 | [Add observability in 3 lines](02-framework-integrations.md) | Beginner | Drop-in integrations for LangChain, OpenAI, Claude, CrewAI |
| 3 | [Build a live dashboard with SSE](03-live-dashboard-sse.md) | Intermediate | Stream events to a terminal or web UI |
| 4 | [Trace a multi-step agent run](04-distributed-tracing.md) | Intermediate | Distributed tracing with auto-generated trace/span IDs |
| 5 | [Get notified when your agent fails](05-error-webhooks.md) | Intermediate | Push alerts via webhooks |
| 6 | [Agent-to-agent communication](06-agent-to-agent-websockets.md) | Advanced | Bidirectional real-time pub/sub with WebSockets |
| 7 | [Production error handling](07-production-error-handling.md) | Advanced | Graceful failures, retries, and rate limits |

Start with Guide 1 if you're new to AxonPush. Jump to Guide 2 if you already use LangChain, OpenAI Agents, Claude, or CrewAI.

Looking for the full API reference? See the [README](../../README.md) for the resource table and method signatures.
