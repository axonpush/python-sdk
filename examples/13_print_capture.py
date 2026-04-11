"""
13 — Print capture (stdout/stderr → AxonPush)

Some AI agent frameworks emit free-form output via ``print()`` instead of
going through a structured logger. ``setup_print_capture()`` patches
``sys.stdout`` and ``sys.stderr`` with a tee stream that (a) still writes to
the original console AND (b) forwards each complete line to AxonPush as an
``agent.log`` event.

Run: uv run 13_print_capture.py
"""

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush
from axonpush.integrations.print_capture import setup_print_capture


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="print-capture-demo")
        channel = client.channels.create(name="agent-stdout", app_id=app.id)
        # Print header BEFORE patching so it doesn't get captured.
        print(f"App: {app.name} | Channel: {channel.name}\n")

        handle = setup_print_capture(
            client,
            channel_id=channel.id,
            agent_id="demo-agent",
            service_name="my-agent",
        )
        try:
            # These print() calls are captured AND still visible on the console.
            print("agent starting up")
            print("step 1: loaded tools = ['web_search', 'calculator']")
            print("step 2: calling model")
            print("step 3: parsing response")
            print("agent done")
        finally:
            handle.unpatch()

        events = client.events.list(channel_id=channel.id, limit=20)
        print(f"\nEvents captured ({len(events)}):")
        for ev in events:
            body = ev.payload.get("body", "")
            print(f"  [{ev.event_type}] {body}")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("\nCleaned up.")


if __name__ == "__main__":
    main()
