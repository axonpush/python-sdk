"""03 — Real-time MQTT.

Subscribe to a channel over AWS IoT Core (MQTT-over-WSS) and watch events
arrive as they're published. Two threads cooperate: the main thread is the
subscriber, a background thread is the publisher. Credentials for the IoT
broker are fetched + auto-rotated by the SDK.

Run::

    uv run examples/03_realtime_mqtt.py
"""

import threading
import time
from typing import Any

from config import APP_ID, BASE_URL, CHANNEL_ID, ENVIRONMENT, require_credentials

require_credentials()

from axonpush import AxonPush, EventType  # noqa: E402


def publish_loop(client: AxonPush, channel_id: str, app_id: str, stop: threading.Event) -> None:
    time.sleep(1.0)
    steps = [
        ("agent.init", {"status": "booting"}, EventType.AGENT_START),
        ("tool.search", {"query": "latest AI news"}, EventType.AGENT_TOOL_CALL_START),
        ("tool.search", {"results": 5}, EventType.AGENT_TOOL_CALL_END),
        ("agent.think", {"thought": "summarising results"}, EventType.AGENT_MESSAGE),
        ("agent.done", {"output": "summary generated"}, EventType.AGENT_END),
    ]
    for identifier, payload, event_type in steps:
        if stop.is_set():
            return
        print(f"[publisher] {identifier}")
        client.events.publish(
            identifier, payload, channel_id,
            agent_id="demo-agent",
            event_type=event_type,
        )
        time.sleep(0.6)
    time.sleep(0.5)
    stop.set()


def main() -> None:
    with AxonPush(base_url=BASE_URL, environment=ENVIRONMENT) as client:
        owns_app = APP_ID is None
        owns_channel = CHANNEL_ID is None
        app_id = APP_ID
        channel_id = CHANNEL_ID
        if owns_app:
            app = client.apps.create(name="mqtt-demo")
            assert app is not None
            app_id = app.id
        if owns_channel:
            assert app_id is not None
            channel = client.channels.create("live-stream", app_id)
            assert channel is not None
            channel_id = channel.id
        assert channel_id is not None and app_id is not None
        print(f"app={app_id} channel={channel_id}\n")

        rt = client.connect_realtime(environment=ENVIRONMENT)

        seen = 0

        def on_message(msg: dict[str, Any]) -> None:
            nonlocal seen
            seen += 1
            print(f"  >> [{msg.get('eventType', '?')}] {msg.get('identifier')}: {msg.get('payload')}")

        rt.subscribe(channel_id=channel_id, app_id=app_id, callback=on_message)
        print("[subscriber] listening on MQTT...\n")

        stop = threading.Event()
        pub_thread = threading.Thread(
            target=publish_loop, args=(client, channel_id, app_id, stop), daemon=True
        )
        pub_thread.start()

        # Wait for the publisher to finish then drain a final beat for in-flight
        # broker delivery before disconnecting.
        pub_thread.join()
        time.sleep(1.0)
        rt.disconnect()
        print(f"\n[done] received {seen} message(s) over MQTT.")

        if owns_channel:
            client.channels.delete(channel_id)
        if owns_app:
            client.apps.delete(app_id)


if __name__ == "__main__":
    main()
