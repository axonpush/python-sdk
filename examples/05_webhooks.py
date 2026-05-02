"""05 — Webhooks.

Register a webhook endpoint on a channel, publish an event that matches
the endpoint's filter, then poll the deliveries log.

Set ``WEBHOOK_URL`` (e.g. ``https://webhook.site/<your-id>``) to a real
sink to actually see deliveries arrive — otherwise the default
``https://httpbin.org/post`` will accept them.

Run::

    uv run examples/05_webhooks.py
"""

import time

from config import (
    APP_ID,
    BASE_URL,
    CHANNEL_ID,
    ENVIRONMENT,
    WEBHOOK_URL,
    require_credentials,
)

require_credentials()

from axonpush import AxonPush, EventType  # noqa: E402


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="webhook-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("alerts", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        endpoint = client.webhooks.create_endpoint(
            url=WEBHOOK_URL,
            channel_id=channel_id,
            event_types=["agent.error"],
            description="Error alerting webhook",
        )
        assert endpoint is not None
        endpoint_id = endpoint.endpoint_id
        print(f"Created endpoint: id={endpoint_id} url={endpoint.url}")
        print(f"  Filters: {endpoint.event_types}")
        if endpoint.raw_secret:
            print(f"  Signing secret (shown once): {endpoint.raw_secret}\n")

        client.events.publish(
            "agent.step", {"status": "processing"}, channel_id,
            event_type=EventType.AGENT_MESSAGE,
        )
        print("Published normal event (filtered out)")

        client.events.publish(
            "agent.crash",
            {"error": "ConnectionTimeout", "message": "Failed to reach external API"},
            channel_id,
            event_type=EventType.AGENT_ERROR,
            agent_id="data-fetcher",
        )
        print("Published error event (should trigger delivery)\n")

        print("Waiting for delivery...")
        time.sleep(3.0)

        deliveries = client.webhooks.deliveries(endpoint_id=endpoint_id)
        if deliveries:
            print(f"\n{len(deliveries)} delivery attempt(s):")
            for d in deliveries:
                http_code = int(d.status_code) if d.status_code else "-"
                print(f"  status={d.status} attempts={int(d.attempts)} http={http_code}")
        else:
            print("No deliveries recorded yet (they may still be in flight).")

        client.webhooks.delete_endpoint(endpoint_id=endpoint_id)
        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
