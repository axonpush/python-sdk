import time
import uuid

from axonpush import EventType
from axonpush.models.events import Event


class TestEventsResource:
    def test_publish_event(self, client, channel):
        event = client.events.publish(
            "test_action",
            {"key": "value"},
            channel_id=channel.id,
            agent_id="test-agent",
            event_type=EventType.AGENT_TOOL_CALL_START,
        )
        assert isinstance(event, Event)
        assert event.identifier == "test_action"
        assert event.payload == {"key": "value"}
        assert event.agent_id == "test-agent"
        assert event.event_type == EventType.AGENT_TOOL_CALL_START

    def test_publish_with_string_event_type(self, client, channel):
        event = client.events.publish(
            "string_type_action",
            {"data": 123},
            channel_id=channel.id,
            event_type="agent.tool_call.end",
        )
        assert event.event_type == EventType.AGENT_TOOL_CALL_END

    def test_publish_with_enum_event_type(self, client, channel):
        event = client.events.publish(
            "enum_type_action",
            {"data": "test"},
            channel_id=channel.id,
            event_type=EventType.AGENT_MESSAGE,
        )
        assert event.event_type == EventType.AGENT_MESSAGE

    def test_publish_auto_generates_trace_id(self, client, channel):
        event = client.events.publish(
            "auto_trace",
            {"data": "test"},
            channel_id=channel.id,
        )
        assert event.trace_id is not None
        assert event.trace_id.startswith("tr_")

    def test_publish_with_explicit_trace_id(self, client, channel):
        trace_id = f"tr_{uuid.uuid4().hex[:16]}"
        event = client.events.publish(
            "explicit_trace",
            {"data": "test"},
            channel_id=channel.id,
            trace_id=trace_id,
        )
        assert event.trace_id == trace_id

    def test_publish_with_metadata(self, client, channel):
        meta = {"source": "test", "version": 1}
        event = client.events.publish(
            "meta_action",
            {"data": "test"},
            channel_id=channel.id,
            metadata=meta,
        )
        assert event.metadata == meta

    def test_list_events(self, client, channel):
        client.events.publish(
            "list_test_1",
            {"order": 1},
            channel_id=channel.id,
        )
        events = client.events.list(channel.id)
        assert isinstance(events, list)
        assert all(isinstance(e, Event) for e in events)

    def test_list_events_pagination(self, client, channel):
        for i in range(3):
            client.events.publish(
                f"page_test_{i}",
                {"i": i},
                channel_id=channel.id,
            )
        page1 = client.events.list(channel.id, page=1, limit=2)
        assert len(page1) <= 2
