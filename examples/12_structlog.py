"""
12 — Structlog integration

Structlog is the Python ecosystem's go-to library for structured logging.
This example installs a structlog processor that forwards each event to
AxonPush as an OpenTelemetry-shaped ``app.log``. The processor is
non-destructive — it does not modify the event dict, so it composes
cleanly with the rest of your processor chain.

Run: uv sync --extra structlog
     uv run 12_structlog.py
"""

import sys

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush

try:
    import structlog
    from axonpush.integrations.structlog import axonpush_structlog_processor
except ImportError:
    print("Install structlog integration: uv sync --extra structlog")
    sys.exit(1)


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="structlog-demo")
        channel = client.channels.create(name="service-logs", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        forwarder = axonpush_structlog_processor(
            client=client,
            channel_id=channel.id,
            service_name="my-api",
            environment="dev",
        )

        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                forwarder,
                structlog.dev.ConsoleRenderer(),
            ],
        )

        log = structlog.get_logger("my_app")
        log.info("user signed in", user_id=42, method="oauth")
        log.warning("rate limit approaching", endpoint="/api/search", remaining=3)
        log.error("downstream timeout", endpoint="/api/search", elapsed_ms=5000)

        forwarder.flush(timeout=5.0)

        events = client.events.list(channel_id=channel.id, limit=20)
        print(f"\nEvents published ({len(events)}):")
        for ev in events:
            sev = ev.payload.get("severityText", "?")
            body = ev.payload.get("body", "")
            print(f"  [{sev}] {ev.identifier}: {body}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")

        forwarder.close()
        # Reset structlog so downstream examples in the same process don't
        # inherit our processor chain.
        structlog.reset_defaults()


if __name__ == "__main__":
    main()
