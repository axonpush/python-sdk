# Add Observability to Your AI Agent in 3 Lines

> Drop-in integrations for LangChain, OpenAI Agents, Claude, and CrewAI. No manual instrumentation required.

## The Problem

You're using a framework to build your agent. You want to see every chain step, tool call, and LLM interaction — without wrapping each one in custom logging. You need observability that plugs into your existing code, not a rewrite.

## The Solution

Install the integration you need:

```bash
pip install axonpush[langchain]       # LangChain / LangGraph
pip install axonpush[openai-agents]   # OpenAI Agents SDK
pip install axonpush[anthropic]       # Claude / Anthropic
pip install axonpush[crewai]          # CrewAI
```

### LangChain / LangGraph

```python
from axonpush import AxonPush
from axonpush.integrations.langchain import AxonPushCallbackHandler

client = AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz")
handler = AxonPushCallbackHandler(client, channel_id=1, agent_id="my-agent")

# Every chain, tool, and LLM event is published automatically
chain.invoke({"input": "research AI frameworks"}, config={"callbacks": [handler]})
```

### OpenAI Agents SDK

```python
from axonpush import AsyncAxonPush
from axonpush.integrations.openai_agents import AxonPushRunHooks

client = AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz")
hooks = AxonPushRunHooks(client, channel_id=1)

result = await Runner.run(agent, input="research AI frameworks", hooks=hooks)
```

### Claude / Anthropic

```python
from axonpush import AxonPush
from axonpush.integrations.anthropic import AxonPushAnthropicTracer

client = AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz")
tracer = AxonPushAnthropicTracer(client, channel_id=1)

# Wraps messages.create() — auto-emits events for tool_use, text, and turns
response = tracer.create_message(
    anthropic_client,
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Research AI frameworks"}],
)
```

### CrewAI

```python
from axonpush import AxonPush
from axonpush.integrations.crewai import AxonPushCrewCallbacks

client = AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz")
callbacks = AxonPushCrewCallbacks(client, channel_id=1)

callbacks.on_crew_start()
result = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    step_callback=callbacks.on_step,
    task_callback=callbacks.on_task_complete,
).kickoff()
callbacks.on_crew_end(result)
```

## What Just Happened

- Each integration maps framework-specific lifecycle events to AxonPush event types automatically.
- **LangChain** publishes `chain.start`, `chain.end`, `llm.start`, `llm.end`, `tool.<name>.start`, `tool.end`, and error events via the callback protocol.
- **OpenAI Agents** publishes `agent.run.start`, `agent.run.end`, `tool.<name>.start`, `tool.<name>.end`, and `agent.handoff` events via run hooks.
- **Anthropic** wraps `messages.create()` to emit `conversation.turn`, `tool.<name>.start`, `agent.response`, and `tool.result` events.
- **CrewAI** uses step and task callbacks to emit `crew.start`, `agent.step`, `task.complete`, and `crew.end` events.
- All integrations auto-generate trace and span IDs so events are correlated by default.

<details>
<summary><strong>Go Deeper</strong></summary>

### Customizing agent ID and trace ID

Every integration accepts `agent_id` and `trace_id` parameters:

```python
# LangChain — custom agent ID and trace correlation
handler = AxonPushCallbackHandler(
    client,
    channel_id=1,
    agent_id="researcher-v2",
    trace_id="tr_pipeline_run_99",   # correlate with other services
    metadata={"env": "production"},
)
```

### Cross-service trace correlation

Pass the same `trace_id` across services to build a unified trace:

```python
# Service A: LangChain agent
handler = AxonPushCallbackHandler(client, channel_id=1, trace_id="tr_shared_123")

# Service B: OpenAI agent consuming Service A's output
hooks = AxonPushRunHooks(client, channel_id=2, trace_id="tr_shared_123")
```

Both services' events appear in the same trace when you call `client.traces.get_events("tr_shared_123")`.

### Anthropic async variant

```python
# Use acreate_message for async Anthropic clients
response = await tracer.acreate_message(
    async_anthropic_client,
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello"}],
)

# Manually emit tool result events
await tracer.asend_tool_result(tool_use_id="toolu_abc", result={"answer": 42})
```

### Events published by each integration

| Framework | Events |
|-----------|--------|
| LangChain | `chain.start`, `chain.end`, `chain.error`, `llm.start`, `llm.end`, `llm.token`, `tool.<name>.start`, `tool.end`, `tool.error` |
| OpenAI Agents | `agent.run.start`, `agent.run.end`, `tool.<name>.start`, `tool.<name>.end`, `agent.handoff` |
| Anthropic | `conversation.turn`, `tool.<name>.start`, `agent.response`, `tool.result` |
| CrewAI | `crew.start`, `crew.end`, `agent.step`, `tool.<name>.start`, `tool.<name>.end`, `task.complete` |

</details>

## Next Steps

- [Stream these events live with SSE](03-live-dashboard-sse.md)
- [Trace a multi-step run end-to-end](04-distributed-tracing.md)
- [See what your agent is doing — the basics](01-realtime-agent-events.md)
