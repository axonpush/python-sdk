"""13 — Print capture.

Some agent frameworks emit free-form output via ``print()`` rather than
through a structured logger. ``setup_print_capture()`` patches
``sys.stdout`` / ``sys.stderr`` with a tee that (a) still writes to the
original console and (b) forwards each completed line to AxonPush as an
``agent.log`` event.

Run::

    uv run examples/13_print_capture.py
"""

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush  # noqa: E402
from axonpush.integrations.print_capture import setup_print_capture  # noqa: E402


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="print-capture-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("agent-stdout", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None

        # Print the header BEFORE patching so it doesn't get captured.
        print(f"channel={channel_id}\n")

        handle = setup_print_capture(
            client, channel_id,
            agent_id="demo-agent",
            service_name="my-agent",
        )
        try:
            print("agent starting up")
            print("step 1: loaded tools = ['web_search', 'calculator']")
            print("step 2: calling model")
            print("step 3: parsing response")
            print("agent done")
            handle.flush(timeout=5.0)
        finally:
            handle.unpatch()

        listing = client.events.list(channel_id, limit=20)
        if listing is not None:
            print(f"\nEvents captured ({len(listing.data)}):")
            for ev in listing.data:
                props = ev.payload.additional_properties if ev.payload else {}
                body = props.get("body", "")
                print(f"  [{ev.event_type}] {body}")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app and app_id is not None:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
