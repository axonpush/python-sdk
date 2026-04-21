"""
01 — Quickstart

Create an app, a channel, publish events, list them, then clean up.
Run: uv run 01_quickstart.py
"""

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush, EventType


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        # 1. Create an app
        app = client.apps.create(name="quickstart-demo")
        print(f"Created app: {app.name} (id={app.id})")

        # 2. Create a channel on that app
        channel = client.channels.create(name="events", app_id=app.id)
        print(f"Created channel: {channel.name} (id={channel.id})")

        # 3. Publish events. These are async-ingested by the server — publish()
        # returns with queued=True within a few ms, and id/created_at are populated
        # once the write lands (visible via events.list() below).
        e1 = client.events.publish(
            identifier="task.started",
            payload={"task": "summarize article", "url": "https://example.com"},
            channel_id=channel.id,
            agent_id="research-agent",
            event_type=EventType.AGENT_START,
        )
        print(f"Published: {e1.identifier} (queued={e1.queued})")

        e2 = client.events.publish(
            identifier="task.progress",
            payload={"progress": 50, "status": "fetching content"},
            channel_id=channel.id,
            agent_id="research-agent",
            event_type=EventType.CUSTOM,
        )
        print(f"Published: {e2.identifier} (queued={e2.queued})")

        e3 = client.events.publish(
            identifier="task.completed",
            payload={"summary": "Article discusses AI advancements in 2025."},
            channel_id=channel.id,
            agent_id="research-agent",
            event_type=EventType.AGENT_END,
        )
        print(f"Published: {e3.identifier} (queued={e3.queued})")

        # 4. List events
        events = client.events.list(channel_id=channel.id)
        print(f"\nChannel has {len(events)} events:")
        for ev in events:
            print(f"  [{ev.event_type}] {ev.identifier} — {ev.payload}")

        # 5. Clean up
        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up resources.")


if __name__ == "__main__":
    main()
