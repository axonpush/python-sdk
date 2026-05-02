"""12 — Structlog integration.

``axonpush_structlog_processor`` is a structlog processor. Drop it into
your processor chain and every event_dict gets forwarded to AxonPush as
an ``app.log`` event. The processor is non-destructive — it does not
touch the event_dict, so it composes cleanly with the rest of your chain.

Run::

    uv sync --extra structlog
    uv run examples/12_structlog.py
"""

import sys

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402

try:
    import structlog

    from axonpush.integrations.structlog import axonpush_structlog_processor
except ImportError:
    print("Install structlog integration: uv sync --extra structlog")
    sys.exit(1)


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="structlog-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("service-logs", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        forwarder = axonpush_structlog_processor(
            client=client,
            channel_id=channel_id,
            service_name="my-api",
            environment=ENVIRONMENT or "dev",
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

        listing = client.events.list(channel_id, limit=20)
        if listing is not None:
            print(f"\nEvents published ({len(listing.data)}):")
            for ev in listing.data:
                props = ev.payload.additional_properties if ev.payload else {}
                sev = props.get("severityText", "?")
                body = props.get("body", "")
                print(f"  [{sev}] {ev.identifier}: {body}")

        forwarder.close()
        # Prevent downstream examples in the same process from inheriting the
        # processor chain we just installed.
        structlog.reset_defaults()

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
