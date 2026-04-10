import threading
import time

import pytest

from axonpush import EventType
from axonpush.models.events import Event
from axonpush.realtime.sse import SSESubscription

pytestmark = pytest.mark.e2e


class TestSSESubscription:
    def test_receive_event_via_sse(self, client, channel):
        received = []

        def subscriber():
            sub = SSESubscription(client._transport, channel.id)
            with sub as s:
                for event in s:
                    received.append(event)
                    break

        t = threading.Thread(target=subscriber, daemon=True)
        t.start()
        time.sleep(1)

        client.events.publish(
            "sse_test",
            {"msg": "hello"},
            channel_id=channel.id,
            agent_id="sse-agent",
        )

        t.join(timeout=5)
        assert len(received) >= 1
        assert isinstance(received[0], Event)
        assert received[0].identifier == "sse_test"

    def test_sse_with_event_identifier_filter(self, client, channel):
        received = []

        def subscriber():
            sub = SSESubscription(
                client._transport,
                channel.id,
                event_identifier="filtered_event",
            )
            with sub as s:
                for event in s:
                    received.append(event)
                    break

        t = threading.Thread(target=subscriber, daemon=True)
        t.start()
        time.sleep(1)

        client.events.publish(
            "other_event",
            {"msg": "should not match"},
            channel_id=channel.id,
        )
        client.events.publish(
            "filtered_event",
            {"msg": "should match"},
            channel_id=channel.id,
        )

        t.join(timeout=5)
        assert len(received) >= 1
        assert received[0].identifier == "filtered_event"

    def test_sse_with_agent_filter(self, client, channel):
        received = []

        def subscriber():
            sub = SSESubscription(
                client._transport,
                channel.id,
                agent_id="specific-agent",
            )
            with sub as s:
                for event in s:
                    received.append(event)
                    break

        t = threading.Thread(target=subscriber, daemon=True)
        t.start()
        time.sleep(1)

        client.events.publish(
            "agent_filter_test",
            {"msg": "targeted"},
            channel_id=channel.id,
            agent_id="specific-agent",
        )

        t.join(timeout=5)
        assert len(received) >= 1
        assert received[0].agent_id == "specific-agent"

    def test_sse_with_event_type_filter(self, client, channel):
        received = []

        def subscriber():
            sub = SSESubscription(
                client._transport,
                channel.id,
                event_type=EventType.AGENT_ERROR,
            )
            with sub as s:
                for event in s:
                    received.append(event)
                    break

        t = threading.Thread(target=subscriber, daemon=True)
        t.start()
        time.sleep(1)

        client.events.publish(
            "error_event",
            {"error": "something broke"},
            channel_id=channel.id,
            event_type=EventType.AGENT_ERROR,
        )

        t.join(timeout=5)
        assert len(received) >= 1
        assert received[0].event_type == EventType.AGENT_ERROR
