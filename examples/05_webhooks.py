"""
05 — Webhooks

Create a webhook endpoint, publish events, and check delivery status.
Run: uv run 05_webhooks.py

Set WEBHOOK_URL in .env to a real endpoint (e.g., https://webhook.site/your-id)
to see actual deliveries.
"""

import time

from config import API_KEY, TENANT_ID, BASE_URL, WEBHOOK_URL, require_credentials

require_credentials()

from axonpush import AxonPush, EventType


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="webhook-demo")
        channel = client.channels.create(name="alerts", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        # 1. Create a webhook endpoint that listens for errors
        endpoint = client.webhooks.create_endpoint(
            url=WEBHOOK_URL,
            channel_id=channel.id,
            event_types=["agent.error"],
            description="Error alerting webhook",
        )
        print(f"Webhook endpoint created: id={endpoint.id}")
        print(f"  URL: {endpoint.url}")
        print(f"  Filters: {endpoint.event_types}\n")

        # 2. Publish a normal event (should NOT trigger webhook)
        client.events.publish(
            identifier="agent.step", payload={"status": "processing"},
            channel_id=channel.id, event_type=EventType.AGENT_MESSAGE,
        )
        print("Published normal event (should not trigger webhook)")

        # 3. Publish an error event (SHOULD trigger webhook)
        client.events.publish(
            identifier="agent.crash",
            payload={"error": "ConnectionTimeout", "message": "Failed to reach external API after 3 retries"},
            channel_id=channel.id, event_type=EventType.AGENT_ERROR, agent_id="data-fetcher",
        )
        print("Published error event (should trigger webhook)\n")

        # 4. Wait for delivery
        print("Waiting for webhook delivery...")
        time.sleep(3)

        # 5. Check delivery status
        deliveries = client.webhooks.get_deliveries(endpoint_id=endpoint.id)
        if deliveries:
            print(f"\n{len(deliveries)} delivery attempt(s):")
            for d in deliveries:
                print(f"  Status: {d.status} | Attempts: {d.attempts} | HTTP: {d.status_code}")
        else:
            print("No deliveries recorded yet (processing may take a moment).")

        # Clean up
        client.webhooks.delete_endpoint(endpoint_id=endpoint.id)
        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
