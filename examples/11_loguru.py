"""11 — Loguru integration.

Loguru is a popular alternative to stdlib logging. The
``create_axonpush_loguru_sink`` helper returns a callable that you pass to
``logger.add(sink, serialize=True)``. ``serialize=True`` is required —
Loguru hands the sink a JSON string, which the sink then parses.

Run::

    uv sync --extra loguru
    uv run examples/11_loguru.py
"""

import sys

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402

try:
    from loguru import logger

    from axonpush.integrations.loguru import create_axonpush_loguru_sink
except ImportError:
    print("Install Loguru integration: uv sync --extra loguru")
    sys.exit(1)


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="loguru-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("service-logs", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        sink = create_axonpush_loguru_sink(
            client=client,
            channel_id=channel_id,
            service_name="my-api",
            environment=ENVIRONMENT or "dev",
        )
        sink_id = logger.add(sink, serialize=True)

        logger.info("user signed in", user_id=42, method="oauth")
        logger.warning("rate limit approaching", endpoint="/api/search", remaining=3)
        try:
            raise RuntimeError("downstream timeout")
        except RuntimeError:
            logger.exception("search backend failed", endpoint="/api/search")

        sink.flush(timeout=5.0)
        logger.remove(sink_id)
        sink.close()

        listing = client.events.list(channel_id, limit=20)
        if listing is not None:
            print(f"\nEvents published ({len(listing.data)}):")
            for ev in listing.data:
                props = ev.payload.additional_properties if ev.payload else {}
                sev = props.get("severityText", "?")
                body = props.get("body", "")
                print(f"  [{sev}] {ev.identifier}: {body}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
