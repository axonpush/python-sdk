"""10 — Stdlib logging handler.

Ship records emitted via Python's built-in ``logging`` to AxonPush as
OpenTelemetry-shaped ``app.log`` events. This is the integration most
backend services want — FastAPI, Flask, and Django all funnel through
stdlib logging.

The handler installs a self-recursion filter that drops records from
``httpx`` / ``httpcore`` / ``axonpush`` so a publish never loops back
through the handler.

Run::

    uv run examples/10_stdlib_logging.py
"""

import logging

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.logging_handler import AxonPushLoggingHandler  # noqa: E402


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="stdlib-logging-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("service-logs", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        handler = AxonPushLoggingHandler(
            client=client,
            channel_id=channel_id,
            service_name="my-api",
            environment=ENVIRONMENT or "dev",
        )

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)

        log = logging.getLogger("my_app.orders")
        log.info("order created", extra={"order_id": 1234, "total": 49.99})
        log.warning("stock low for sku=%s", "A-42", extra={"remaining": 3})
        try:
            raise RuntimeError("payment gateway timeout")
        except RuntimeError:
            log.exception("failed to charge card", extra={"order_id": 1234})

        # Drain in-flight HTTP calls before tearing down the channel/app so
        # the publish race doesn't drop the last record.
        handler.flush(timeout=5.0)
        root.removeHandler(handler)
        handler.close()

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


# --- Django integration snippet (reference) --------------------------------
#
# Add this to ``settings.py`` to wire the handler via dictConfig. The handler
# reads AXONPUSH_API_KEY / AXONPUSH_TENANT_ID from the environment if you
# don't pass an explicit ``client``.
#
#     LOGGING = {
#         "version": 1,
#         "disable_existing_loggers": False,
#         "handlers": {
#             "axonpush": {
#                 "class": "axonpush.integrations.logging_handler.AxonPushLoggingHandler",
#                 "channel_id": "ch_…",
#                 "service_name": "my-django-app",
#                 "exclude_loggers": ["django.db.backends"],
#             },
#             "console": {"class": "logging.StreamHandler"},
#         },
#         "root": {"handlers": ["axonpush", "console"], "level": "INFO"},
#     }


if __name__ == "__main__":
    main()
