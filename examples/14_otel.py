"""14 — OpenTelemetry span exporter.

If your service is already instrumented with the OpenTelemetry SDK, plug
``AxonPushSpanExporter`` into your ``TracerProvider``. Every span you
record gets shipped to AxonPush as an ``app.span`` event alongside any
other backends you export to (Jaeger, Tempo, Honeycomb, etc.).

Run::

    uv sync --extra otel
    uv run examples/14_otel.py
"""

import sys

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    from axonpush.integrations.otel import AxonPushSpanExporter
except ImportError:
    print("Install OTel integration: uv sync --extra otel")
    sys.exit(1)


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="otel-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("spans", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        provider = TracerProvider()
        exporter = AxonPushSpanExporter(
            client=client,
            channel_id=channel_id,
            service_name="my-api",
            environment=ENVIRONMENT or "dev",
        )
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("my_app")

        with tracer.start_as_current_span("POST /chat") as req:
            req.set_attribute("http.method", "POST")
            req.set_attribute("http.route", "/chat")

            with tracer.start_as_current_span("llm.call") as llm:
                llm.set_attribute("model", "gpt-4o-mini")
                llm.set_attribute("prompt_tokens", 128)

            with tracer.start_as_current_span("db.query") as db:
                db.set_attribute("db.statement", "SELECT * FROM users WHERE id=$1")
                db.set_attribute("db.rows_affected", 1)

        provider.force_flush()
        provider.shutdown()

        listing = client.events.list(channel_id, limit=20)
        if listing is not None:
            print(f"\nSpans published ({len(listing.data)}):")
            for ev in listing.data:
                props = ev.payload.additional_properties if ev.payload else {}
                name = props.get("name", "?")
                print(f"  [{ev.event_type}] {name}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
