import time

from axonpush import EventType
from axonpush.models.events import Event



class TestWebSocketClient:
    def test_connect_and_disconnect(self, client):
        ws = client.connect_websocket()
        assert ws is not None
        ws.disconnect()

    def test_subscribe_to_channel(self, client, channel):
        ws = client.connect_websocket()
        ws.subscribe(channel_id=channel.id)
        time.sleep(0.5)
        ws.disconnect()

    def test_subscribe_with_filters(self, client, channel):
        ws = client.connect_websocket()
        ws.subscribe(
            channel_id=channel.id,
            agent_id="filter-agent",
            event_type=EventType.AGENT_TOOL_CALL_START,
            trace_id="tr_test123",
        )
        time.sleep(0.5)
        ws.disconnect()

    def test_publish_via_websocket(self, client, channel):
        ws = client.connect_websocket()
        ws.subscribe(channel_id=channel.id)
        time.sleep(0.5)
        ws.publish(
            channel_id=channel.id,
            identifier="ws_publish_test",
            payload={"msg": "from websocket"},
            agent_id="ws-agent",
        )
        time.sleep(0.5)
        ws.disconnect()

    def test_on_event_callback(self, client, channel):
        received = []
        ws = client.connect_websocket()
        ws.on_event(lambda e: received.append(e))
        ws.subscribe(channel_id=channel.id)
        time.sleep(1)

        client.events.publish(
            "ws_callback_test",
            {"msg": "callback"},
            channel_id=channel.id,
            agent_id="callback-agent",
        )
        time.sleep(2)

        ws.disconnect()
        assert len(received) >= 1
        assert isinstance(received[0], Event)

    def test_unsubscribe(self, client, channel):
        ws = client.connect_websocket()
        ws.subscribe(channel_id=channel.id)
        time.sleep(0.5)
        ws.unsubscribe(channel_id=channel.id)
        time.sleep(0.5)
        ws.disconnect()

    def test_publish_with_event_type(self, client, channel):
        ws = client.connect_websocket()
        ws.subscribe(channel_id=channel.id)
        time.sleep(0.5)
        ws.publish(
            channel_id=channel.id,
            identifier="ws_typed",
            payload={"step": "done"},
            event_type=EventType.AGENT_END,
        )
        time.sleep(0.5)
        ws.disconnect()
