"""
14 — OpenTelemetry span exporter

If your service is already instrumented with the OpenTelemetry SDK, add
``AxonPushSpanExporter`` to your tracer provider and every span you create
ships to AxonPush as an ``app.span`` event alongside whatever other OTel
backends you already export to.

Run: uv sync --extra otel
     uv run 14_otel.py
"""

import sys

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from axonpush.integrations.otel import AxonPushSpanExporter
except ImportError:
    print("Install OTel integration: uv sync --extra otel")
    sys.exit(1)


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="otel-demo")
        channel = client.channels.create(name="spans", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}\n")

        provider = TracerProvider()
        provider.add_span_processor(
            SimpleSpanProcessor(
                AxonPushSpanExporter(
                    client=client,
                    channel_id=channel.id,
                    service_name="my-api",
                    environment="dev",
                )
            )
        )
        trace.set_tracer_provider(provider)
        tracer = trace.get_tracer("my_app")

        # Emit a few nested spans to exercise the exporter.
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

        events = client.events.list(channel_id=channel.id, limit=20)
        print(f"\nSpans published ({len(events)}):")
        for ev in events:
            name = ev.payload.get("name", "?")
            print(f"  [{ev.event_type}] {name}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
