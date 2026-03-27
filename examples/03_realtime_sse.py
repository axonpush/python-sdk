"""
03 — Real-time SSE

Subscribe to a channel via Server-Sent Events and watch events arrive in real-time.
Uses two threads: one listens, one publishes.
Run: uv run 03_realtime_sse.py
"""

import json
import time
import threading

from config import API_KEY, TENANT_ID, BASE_URL, require_credentials

require_credentials()

from axonpush import AxonPush, EventType


def listener(client: AxonPush, channel_id: int, stop_event: threading.Event):
    """Subscribe to SSE and print events as they arrive."""
    print("[listener] Connecting to SSE stream...\n")
    try:
        with client.channels.subscribe_sse(channel_id=channel_id) as event_source:
            for event in event_source.iter_sse():
                data = json.loads(event.data)
                print(f"  >> [{data.get('eventType', 'custom')}] {data.get('identifier')} — {data.get('payload')}")
                if stop_event.is_set():
                    break
    except Exception as e:
        if not stop_event.is_set():
            print(f"[listener] Error: {e}")


def publisher(client: AxonPush, channel_id: int, stop_event: threading.Event):
    """Publish events with a delay to simulate real activity."""
    time.sleep(1)

    steps = [
        ("agent.init", {"status": "booting up"}, EventType.AGENT_START),
        ("tool.search", {"query": "latest AI news"}, EventType.AGENT_TOOL_CALL_START),
        ("tool.search", {"results": 5}, EventType.AGENT_TOOL_CALL_END),
        ("agent.think", {"thought": "Let me summarize these results"}, EventType.AGENT_MESSAGE),
        ("agent.done", {"output": "Summary generated"}, EventType.AGENT_END),
    ]

    for identifier, payload, event_type in steps:
        print(f"[publisher] Publishing: {identifier}")
        client.events.publish(
            identifier=identifier, payload=payload,
            channel_id=channel_id, agent_id="demo-agent", event_type=event_type,
        )
        time.sleep(1)

    time.sleep(0.5)
    stop_event.set()


def main():
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as client:
        app = client.apps.create(name="sse-demo")
        channel = client.channels.create(name="live-stream", app_id=app.id)
        print(f"App: {app.name} | Channel: {channel.name}")
        print("Streaming events in real-time:\n")

        stop = threading.Event()
        listen_thread = threading.Thread(target=listener, args=(client, channel.id, stop), daemon=True)
        publish_thread = threading.Thread(target=publisher, args=(client, channel.id, stop))

        listen_thread.start()
        publish_thread.start()
        publish_thread.join()
        time.sleep(1)
        stop.set()

        print("\n[done] Stream ended.")

        client.channels.delete(channel_id=channel.id)
        client.apps.delete(app_id=app.id)
        print("Cleaned up.")


if __name__ == "__main__":
    main()
