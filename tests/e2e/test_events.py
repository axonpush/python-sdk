import uuid

import pytest

from axonpush.models import Event, EventListResponseDto, EventType

pytestmark = pytest.mark.e2e


class TestEvents:
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
        assert event.event_id is not None

    def test_publish_with_string_event_type(self, client, channel):
        event = client.events.publish(
            "string_type_action",
            {"data": 123},
            channel_id=channel.id,
            event_type="agent.tool_call.end",
        )
        assert event is not None
        assert event.identifier == "string_type_action"

    def test_publish_with_enum_event_type(self, client, channel):
        event = client.events.publish(
            "enum_type_action",
            {"data": "test"},
            channel_id=channel.id,
            event_type=EventType.AGENT_MESSAGE,
        )
        assert event is not None

    def test_publish_auto_generates_trace_id(self, client, channel):
        # The SDK will assemble a trace_id when none is supplied. Round-trip
        # through list() to verify it landed.
        client.events.publish(
            "auto_trace",
            {"data": "test"},
            channel_id=channel.id,
        )
        listing = client.events.list(channel.id)
        assert isinstance(listing, EventListResponseDto)
        assert any(
            e.trace_id and e.trace_id.startswith("tr_") for e in listing.data
        )

    def test_publish_with_explicit_trace_id(self, client, channel):
        trace_id = f"tr_{uuid.uuid4().hex[:16]}"
        client.events.publish(
            "explicit_trace",
            {"data": "test"},
            channel_id=channel.id,
            trace_id=trace_id,
        )
        listing = client.events.list(channel.id)
        assert any(e.trace_id == trace_id for e in listing.data)

    def test_publish_with_metadata(self, client, channel):
        meta = {"source": "test", "version": 1}
        ev = client.events.publish(
            "meta_action",
            {"data": "test"},
            channel_id=channel.id,
            metadata=meta,
        )
        assert ev is not None

    def test_list_events(self, client, channel):
        client.events.publish(
            "list_test_1",
            {"order": 1},
            channel_id=channel.id,
        )
        listing = client.events.list(channel.id)
        assert isinstance(listing, EventListResponseDto)
        assert isinstance(listing.data, list)
