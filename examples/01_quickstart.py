"""01 — Quickstart.

Create an app and channel, publish a few events, list them, then clean up.

Run::

    uv run examples/01_quickstart.py
"""

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush, EventType  # noqa: E402


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        # Reuse caller-supplied IDs when present; otherwise spin up scratch resources.
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None

        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="quickstart-demo")
            assert app is not None
            app_id = app.id
            print(f"Created app: {app.name} (id={app.id})")
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("events", app_id)
            assert channel is not None
            channel_id = channel.id
            print(f"Created channel: {channel.name} (id={channel.id})")

        assert channel_id is not None

        # Publishes are async-ingested. The returned Event carries event_id +
        # queued=True within a few ms; the durable shape (with a DB id and
        # full payload) appears via events.list() once the write lands.
        steps = [
            ("task.started", {"task": "summarize article", "url": "https://example.com"},
             EventType.AGENT_START),
            ("task.progress", {"progress": 50, "status": "fetching content"},
             EventType.CUSTOM),
            ("task.completed", {"summary": "Article discusses AI advances in 2026."},
             EventType.AGENT_END),
        ]
        for identifier, payload, event_type in steps:
            ev = client.events.publish(
                identifier, payload, channel_id,
                agent_id="research-agent",
                event_type=event_type,
            )
            assert ev is not None
            print(f"Published: {identifier} (event_id={ev.event_id}, queued={ev.queued})")

        listing = client.events.list(channel_id, limit=10)
        if listing is not None:
            print(f"\nChannel has {len(listing.data)} event(s) listed:")
            for ev in listing.data:
                print(f"  [{ev.event_type}] {ev.identifier}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)
        if owns_app or owns_channel:
            print("\nCleaned up scratch resources.")


if __name__ == "__main__":
    main()
