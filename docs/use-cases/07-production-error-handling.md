# Handle Errors, Retries, and Rate Limits Gracefully

> Ship to production with confidence. Typed exceptions, retry hints, and clean resource management.

## The Problem

Your agent works in development. Now you're deploying to production. API keys expire. Servers have temporary outages. Rate limits get hit when your agent scales. If your code crashes on every transient failure, your users see broken experiences. You need graceful error handling.

## The Solution

```bash
pip install axonpush
```

```python
from axonpush import AxonPush
from axonpush.exceptions import RateLimitError, AuthenticationError, ServerError
import time

with AxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    try:
        event = client.events.publish(
            "web_search", {"query": "AI agents"},
            channel_id=1, agent_id="researcher",
        )
    except RateLimitError as e:
        # Server tells you exactly how long to wait
        print(f"Rate limited. Retry after {e.retry_after}s")
        time.sleep(e.retry_after or 1)
    except AuthenticationError:
        print("Invalid API key — check your credentials")
    except ServerError:
        print("AxonPush is temporarily unavailable — fall back to local logging")
```

## What Just Happened

- AxonPush raises typed exceptions mapped to HTTP status codes. You catch specific errors, not generic ones.
- `RateLimitError` (429) includes `retry_after` — the number of seconds to wait before retrying.
- `AuthenticationError` (401) means your API key is invalid or expired.
- `ServerError` (5xx) means AxonPush itself is having issues. Your agent can fall back gracefully.
- The `with` block ensures the HTTP client is closed cleanly, even if an exception is raised.

<details>
<summary><strong>Go Deeper</strong></summary>

### Full exception hierarchy

```
AxonPushError (base)
├── AuthenticationError    → HTTP 401
├── ForbiddenError         → HTTP 403
├── NotFoundError          → HTTP 404
├── ValidationError        → HTTP 400
├── RateLimitError         → HTTP 429 (includes retry_after)
└── ServerError            → HTTP 5xx
```

All exceptions expose `status_code`:

```python
from axonpush.exceptions import AxonPushError

try:
    client.events.publish(...)
except AxonPushError as e:
    print(f"HTTP {e.status_code}: {e}")
```

### Retry with exponential backoff

```python
from axonpush.exceptions import RateLimitError, ServerError
import time

def publish_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.events.publish(**kwargs)
        except RateLimitError as e:
            wait = e.retry_after or (2 ** attempt)
            time.sleep(wait)
        except ServerError:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed after {max_retries} retries")

event = publish_with_retry(
    client,
    identifier="web_search",
    payload={"query": "AI agents"},
    channel_id=1,
    agent_id="researcher",
)
```

### Catch specific validation errors

```python
from axonpush.exceptions import ValidationError, NotFoundError

try:
    client.channels.get(channel_id=999)
except NotFoundError:
    print("Channel doesn't exist — create it first")

try:
    client.events.publish("", {}, channel_id=1)  # empty identifier
except ValidationError as e:
    print(f"Bad request: {e}")
```

### Combine error handling with tracing

Publish an error event before re-raising so your trace captures the failure:

```python
from axonpush import EventType, get_or_create_trace
from axonpush.exceptions import AxonPushError

trace = get_or_create_trace()

try:
    result = call_external_tool()
except Exception as e:
    # Record the failure in AxonPush before handling it
    try:
        client.events.publish(
            "tool_failure",
            {"error": str(e), "tool": "web_search"},
            channel_id=1,
            agent_id="researcher",
            trace_id=trace.trace_id,
            event_type=EventType.AGENT_ERROR,
        )
    except AxonPushError:
        pass  # don't let observability failures break the agent
    raise
```

### Async error handling

The same exception types work with the async client:

```python
from axonpush import AsyncAxonPush
from axonpush.exceptions import RateLimitError
import asyncio

async with AsyncAxonPush(api_key="ak_...", tenant_id="1", base_url="https://api.axonpush.xyz") as client:
    try:
        event = await client.events.publish(
            "web_search", {"query": "AI agents"},
            channel_id=1, agent_id="researcher",
        )
    except RateLimitError as e:
        await asyncio.sleep(e.retry_after or 1)
```

</details>

## Next Steps

- [Start from the beginning: publish your first event](01-realtime-agent-events.md)
- [Add framework integrations for automatic error tracking](02-framework-integrations.md)
- [Set up webhooks for error alerts](05-error-webhooks.md)
