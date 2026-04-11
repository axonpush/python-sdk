"""
10 — Stdlib logging handler

Ship records from Python's built-in ``logging`` module to AxonPush as
OpenTelemetry-shaped ``app.log`` events. This is the most common path for
backend services — FastAPI, Flask, and Django all use stdlib logging.

The handler installs a self-recursion filter by default that drops records
from ``httpx`` / ``httpcore`` / ``axonpush`` (the SDK's own HTTP transport),
so there's no feedback loop from "publishing a log triggers an HTTP request
which gets logged which publishes another log...".

Run: uv run 10_stdlib_logging.py
"""

import logging

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush
from axonpush.integrations.logging_handler import AxonPushLoggingHandler


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="stdlib-logging-demo")
        channel = client.channels.create(name="service-logs", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        handler = AxonPushLoggingHandler(
            client=client,
            channel_id=channel.id,
            service_name="my-api",
            environment="dev",
        )

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)

        logger = logging.getLogger("my_app.orders")
        logger.info("order created", extra={"order_id": 1234, "total": 49.99})
        logger.warning("stock low for sku=%s", "A-42", extra={"remaining": 3})
        try:
            raise RuntimeError("payment gateway timeout")
        except RuntimeError:
            logger.exception("failed to charge card", extra={"order_id": 1234})

        # Non-blocking publisher: drain pending records before teardown so
        # the in-flight HTTP calls don't race the channel/app deletion.
        handler.flush(timeout=5.0)

        # Detach cleanly so subsequent examples don't inherit the handler.
        root.removeHandler(handler)
        handler.close()

        events = client.events.list(channel_id=channel.id, limit=20)
        print(f"\nEvents published ({len(events)}):")
        for ev in events:
            sev = ev.payload.get("severityText", "?")
            body = ev.payload.get("body", "")
            print(f"  [{sev}] {ev.identifier}: {body}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


# --- Django integration snippet (for reference) -----------------------------
#
# In a Django project, add this to ``settings.py`` to wire the handler via
# ``LOGGING`` dictConfig. No pre-built client is needed — the handler reads
# credentials from AXONPUSH_API_KEY / AXONPUSH_TENANT_ID environment vars,
# or from explicit ``api_key`` / ``tenant_id`` kwargs.
#
#     LOGGING = {
#         "version": 1,
#         "disable_existing_loggers": False,
#         "handlers": {
#             "axonpush": {
#                 "class": "axonpush.integrations.logging_handler.AxonPushLoggingHandler",
#                 "channel_id": 14,
#                 "service_name": "my-django-app",
#                 # Optional: exclude noisy Django sub-loggers from AxonPush
#                 # (they still appear in the console handler).
#                 "exclude_loggers": ["django.db.backends"],
#             },
#             "console": {"class": "logging.StreamHandler"},
#         },
#         "root": {"handlers": ["axonpush", "console"], "level": "INFO"},
#     }


if __name__ == "__main__":
    main()
