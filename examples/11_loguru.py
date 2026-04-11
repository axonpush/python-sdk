"""
11 — Loguru integration

Loguru is a popular alternative to stdlib logging that's loved for its
ergonomic API. This example wires a Loguru sink that forwards records to
AxonPush as ``app.log`` events.

Run: uv sync --extra loguru
     uv run 11_loguru.py
"""

import sys

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush

try:
    from loguru import logger
    from axonpush.integrations.loguru import create_axonpush_loguru_sink
except ImportError:
    print("Install Loguru integration: uv sync --extra loguru")
    sys.exit(1)


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="loguru-demo")
        channel = client.channels.create(name="service-logs", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        sink = create_axonpush_loguru_sink(
            client=client,
            channel_id=channel.id,
            service_name="my-api",
            environment="dev",
        )
        # ``serialize=True`` is required — Loguru passes a JSON string of the
        # record to the sink, which the AxonPush sink parses.
        sink_id = logger.add(sink, serialize=True)

        logger.info("user signed in", user_id=42, method="oauth")
        logger.warning("rate limit approaching", endpoint="/api/search", remaining=3)
        try:
            raise RuntimeError("downstream timeout")
        except RuntimeError:
            logger.exception("search backend failed", endpoint="/api/search")

        logger.remove(sink_id)

        events = client.events.list(channel_id=channel.id, limit=20)
        print(f"\nEvents published ({len(events)}):")
        for ev in events:
            sev = ev.payload.get("severityText", "?")
            body = ev.payload.get("body", "")
            print(f"  [{sev}] {ev.identifier}: {body}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
