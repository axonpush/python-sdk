"""Topic builder unit tests — pin the exact MQTT topic shape.

Topic shape (since 0.2.0):
    axonpush/{org}/{envSlug}/{app}/{channel}/{eventType}/{agentId}

The env slot sits between org and app. On subscribe, missing slots fall back
to ``+`` (wildcard); on publish, missing slots fall back to ``_`` (except env,
which falls back to literal ``default`` so AWS IoT routes to the org's
default env). All segments pass through ``[^a-zA-Z0-9_-] -> _`` sanitisation
to satisfy IoT topic-name rules — so e.g. ``agent.error`` is encoded as
``agent_error`` on the wire (the backend's topic-builder applies the same
transform, so they match).
"""
from __future__ import annotations

from axonpush.models.events import EventType
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic


class TestBuildSubscribeTopic:
    def test_full_filter_with_env(self):
        assert (
            build_subscribe_topic(
                "org_1",
                "app_2",
                "ch_3",
                event_type="agent.start",
                agent_id="bot",
                environment="prod",
            )
            == "axonpush/org_1/prod/app_2/ch_3/agent_start/bot"
        )

    def test_event_type_enum_serialized_to_value_then_sanitized(self):
        assert (
            build_subscribe_topic(
                "org_1",
                "app_2",
                "ch_3",
                event_type=EventType.AGENT_TOOL_CALL_START,
                agent_id="bot",
                environment="dev",
            )
            == "axonpush/org_1/dev/app_2/ch_3/agent_tool_call_start/bot"
        )

    def test_no_env_uses_plus_wildcard(self):
        assert (
            build_subscribe_topic(
                "org_1", "app_2", "ch_3", event_type="agent.start", agent_id="bot"
            )
            == "axonpush/org_1/+/app_2/ch_3/agent_start/bot"
        )

    def test_no_event_type_uses_plus_wildcard(self):
        assert (
            build_subscribe_topic(
                "org_1", "app_2", "ch_3", agent_id="bot", environment="dev"
            )
            == "axonpush/org_1/dev/app_2/ch_3/+/bot"
        )

    def test_no_agent_id_uses_plus_wildcard(self):
        assert (
            build_subscribe_topic(
                "org_1", "app_2", "ch_3", event_type="agent.error", environment="dev"
            )
            == "axonpush/org_1/dev/app_2/ch_3/agent_error/+"
        )

    def test_all_optional_omitted(self):
        assert (
            build_subscribe_topic("org_1", "app_2", "ch_3")
            == "axonpush/org_1/+/app_2/ch_3/+/+"
        )

    def test_everything_omitted(self):
        assert build_subscribe_topic("org_1") == "axonpush/org_1/+/+/+/+/+"


class TestBuildPublishTopic:
    def test_publish_with_env(self):
        assert (
            build_publish_topic(
                "org_1",
                "app_2",
                "ch_3",
                event_type=EventType.AGENT_END,
                agent_id="bot",
                environment="prod",
            )
            == "axonpush/org_1/prod/app_2/ch_3/agent_end/bot"
        )

    def test_publish_without_env_uses_default_slug(self):
        assert (
            build_publish_topic(
                "org_1", "app_2", "ch_3", event_type=EventType.AGENT_END, agent_id="bot"
            )
            == "axonpush/org_1/default/app_2/ch_3/agent_end/bot"
        )

    def test_publish_without_agent_falls_to_underscore(self):
        # Publish (vs subscribe) uses '_' for missing agentId — matches
        # AWS IoT-side topic-builder.
        assert (
            build_publish_topic(
                "org_1", "app_2", "ch_3", event_type="custom", environment="dev"
            )
            == "axonpush/org_1/dev/app_2/ch_3/custom/_"
        )

    def test_publish_topic_string_event_type(self):
        assert (
            build_publish_topic(
                "org_x", "app_y", "ch_z", event_type="custom.thing", environment="staging"
            )
            == "axonpush/org_x/staging/app_y/ch_z/custom_thing/_"
        )

    def test_unsafe_chars_sanitized(self):
        # Slashes/spaces/'#' all collapse to '_'.
        assert (
            build_publish_topic(
                "org/1", "app 2", "ch#3", event_type="custom", environment="my env"
            )
            == "axonpush/org_1/my_env/app_2/ch_3/custom/_"
        )
