# Get Notified When Your Agent Fails

> Push error alerts to Slack, Discord, or any HTTP endpoint. Stop babysitting your agents.

## The Problem

Your agent runs on a schedule or serves users in production. You can't sit there watching an SSE stream all day. When something breaks — a tool call fails, an API times out, an agent loops — you need a push notification. A Slack message, a Discord alert, a PagerDuty trigger.

## The Solution

```bash
pip install axonpush
```

```python
from axonpush import AxonPush

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    # Create a webhook that fires on agent errors
    endpoint = client.webhooks.create_endpoint(
        url="https://your-server.com/webhook",
        channel_id=1,
        event_types=["agent.error"],
        secret="whsec_your_signing_secret",
        description="Slack alert on agent errors",
    )

    print(f"Webhook {endpoint.id} active: {endpoint.active}")

    # Check if deliveries are landing
    deliveries = client.webhooks.get_deliveries(endpoint_id=endpoint.id)
    for d in deliveries:
        print(f"  Delivery {d.id}: {d.status} (HTTP {d.status_code})")
```

## What Just Happened

- `create_endpoint()` registers a URL that AxonPush will POST to whenever a matching event is published on the channel.
- `event_types=["agent.error"]` filters the webhook to only fire on error events. Without this, it fires on every event.
- The `secret` enables HMAC signature verification so your server can validate that the request came from AxonPush.
- `get_deliveries()` returns delivery attempts with status (`pending`, `success`, `failed`, `retrying`), HTTP status code, and any error message.
- Failed deliveries are retried automatically.

<details>
<summary><strong>Go Deeper</strong></summary>

### Manage webhook endpoints

```python
# List all webhooks on a channel
endpoints = client.webhooks.list_endpoints(channel_id=1)
for ep in endpoints:
    print(f"{ep.id}: {ep.url} — active={ep.active}, types={ep.event_types}")

# Delete a webhook
client.webhooks.delete_endpoint(endpoint_id=endpoint.id)
```

### Filter by multiple event types

Pass a list to capture specific combinations:

```python
endpoint = client.webhooks.create_endpoint(
    url="https://your-server.com/webhook",
    channel_id=1,
    event_types=["agent.error", "agent.handoff", "agent.end"],
    description="Alert on errors, handoffs, and completions",
)
```

### Available event types for filtering

| Event type | Fires when |
|------------|-----------|
| `agent.start` | Agent begins a run |
| `agent.end` | Agent completes a run |
| `agent.message` | Agent produces a message |
| `agent.tool_call.start` | Agent invokes a tool |
| `agent.tool_call.end` | Tool returns a result |
| `agent.error` | Something went wrong |
| `agent.handoff` | Agent delegates to another |
| `agent.llm.token` | Streaming token from LLM |
| `custom` | Custom event type |

### Monitor delivery health

```python
deliveries = client.webhooks.get_deliveries(endpoint_id=endpoint.id)
for d in deliveries:
    if d.status == "failed":
        print(f"Failed delivery {d.id}: {d.error}")
        print(f"  Attempts: {d.attempts}, Last status: {d.status_code}")
        print(f"  Response: {d.response_body}")
```

The `DeliveryStatus` enum values are: `pending`, `success`, `failed`, `retrying`.

### Async variant

```python
async with AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    endpoint = await client.webhooks.create_endpoint(
        url="https://your-server.com/webhook",
        channel_id=1,
        event_types=["agent.error"],
    )

    deliveries = await client.webhooks.get_deliveries(endpoint_id=endpoint.id)
```

</details>

## Next Steps

- [Build agent-to-agent communication with WebSockets](06-agent-to-agent-websockets.md)
- [Handle errors and rate limits in your code](07-production-error-handling.md)
- [Stream events live with SSE](03-live-dashboard-sse.md)
