"""Topic builder unit tests — pin the exact MQTT topic shape."""
from __future__ import annotations

from axonpush.models.events import EventType
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic


class TestBuildSubscribeTopic:
    def test_full_filter(self):
        assert (
            build_subscribe_topic(
                "org_1", "app_2", "ch_3", event_type="agent.start", agent_id="bot"
            )
            == "axonpush/org_1/app_2/ch_3/agent.start/bot"
        )

    def test_event_type_enum_serialized_to_value(self):
        assert (
            build_subscribe_topic(
                "org_1",
                "app_2",
                "ch_3",
                event_type=EventType.AGENT_TOOL_CALL_START,
                agent_id="bot",
            )
            == "axonpush/org_1/app_2/ch_3/agent.tool_call.start/bot"
        )

    def test_no_event_type_uses_plus_wildcard(self):
        assert (
            build_subscribe_topic("org_1", "app_2", "ch_3", agent_id="bot")
            == "axonpush/org_1/app_2/ch_3/+/bot"
        )

    def test_no_agent_id_uses_plus_wildcard(self):
        assert (
            build_subscribe_topic("org_1", "app_2", "ch_3", event_type="agent.error")
            == "axonpush/org_1/app_2/ch_3/agent.error/+"
        )

    def test_neither_optional_field(self):
        assert (
            build_subscribe_topic("org_1", "app_2", "ch_3")
            == "axonpush/org_1/app_2/ch_3/+/+"
        )


class TestBuildPublishTopic:
    def test_publish_uses_concrete_event_type(self):
        assert (
            build_publish_topic(
                "org_1", "app_2", "ch_3", event_type=EventType.AGENT_END, agent_id="bot"
            )
            == "axonpush/org_1/app_2/ch_3/agent.end/bot"
        )

    def test_publish_without_agent_falls_to_plus(self):
        assert (
            build_publish_topic(
                "org_1", "app_2", "ch_3", event_type="custom"
            )
            == "axonpush/org_1/app_2/ch_3/custom/+"
        )

    def test_publish_topic_string_event_type(self):
        assert (
            build_publish_topic("org_x", "app_y", "ch_z", event_type="custom.thing")
            == "axonpush/org_x/app_y/ch_z/custom.thing/+"
        )
