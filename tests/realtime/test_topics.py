"""Topic builder unit tests — pin the exact MQTT topic shape.

Wire format (matches backend ``easy-push/src/pubsub/topic-builder.ts``)::

    {topic_prefix}/{env_slug}/{app_id}/{channel_id}/{event_type}/{agent_id}

``topic_prefix`` is org-scoped (``"axonpush/{org_id}"``) and is returned
verbatim from ``/auth/iot-credentials``. Sanitisation is identical on
both sides: ``[^a-zA-Z0-9_-] -> _``.
"""

from __future__ import annotations

from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic

ORG_PREFIX = "axonpush/org_1"


class TestBuildSubscribeTopic:
    def test_full_filter(self) -> None:
        assert (
            build_subscribe_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.start",
                agent_id="bot",
                env_slug="prod",
            )
            == "axonpush/org_1/prod/app_2/ch_3/agent_start/bot"
        )

    def test_event_type_with_dots_sanitised(self) -> None:
        assert (
            build_subscribe_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.tool_call.start",
                agent_id="bot",
                env_slug="dev",
            )
            == "axonpush/org_1/dev/app_2/ch_3/agent_tool_call_start/bot"
        )

    def test_no_env_uses_plus(self) -> None:
        assert (
            build_subscribe_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.start",
                agent_id="bot",
            )
            == "axonpush/org_1/+/app_2/ch_3/agent_start/bot"
        )

    def test_no_event_type_uses_plus(self) -> None:
        assert (
            build_subscribe_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                agent_id="bot",
                env_slug="dev",
            )
            == "axonpush/org_1/dev/app_2/ch_3/+/bot"
        )

    def test_no_agent_uses_plus(self) -> None:
        assert (
            build_subscribe_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.error",
                env_slug="dev",
            )
            == "axonpush/org_1/dev/app_2/ch_3/agent_error/+"
        )

    def test_all_optional_omitted(self) -> None:
        assert (
            build_subscribe_topic(ORG_PREFIX, app_id="app_2", channel_id="ch_3")
            == "axonpush/org_1/+/app_2/ch_3/+/+"
        )

    def test_everything_omitted(self) -> None:
        assert build_subscribe_topic(ORG_PREFIX) == "axonpush/org_1/+/+/+/+/+"


class TestBuildPublishTopic:
    def test_with_env(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.end",
                agent_id="bot",
                env_slug="prod",
            )
            == "axonpush/org_1/prod/app_2/ch_3/agent_end/bot"
        )

    def test_no_env_falls_back_to_default_slug(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.end",
                agent_id="bot",
            )
            == "axonpush/org_1/default/app_2/ch_3/agent_end/bot"
        )

    def test_no_env_uses_caller_default_slug(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="agent.end",
                agent_id="bot",
                default_env_slug="staging",
            )
            == "axonpush/org_1/staging/app_2/ch_3/agent_end/bot"
        )

    def test_no_agent_falls_to_underscore(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app_2",
                channel_id="ch_3",
                event_type="custom",
                env_slug="dev",
            )
            == "axonpush/org_1/dev/app_2/ch_3/custom/_"
        )

    def test_dots_in_event_type_sanitised(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app_y",
                channel_id="ch_z",
                event_type="custom.thing",
                env_slug="staging",
            )
            == "axonpush/org_1/staging/app_y/ch_z/custom_thing/_"
        )

    def test_unsafe_chars_sanitised(self) -> None:
        assert (
            build_publish_topic(
                ORG_PREFIX,
                app_id="app 2",
                channel_id="ch#3",
                event_type="custom",
                env_slug="my env",
            )
            == "axonpush/org_1/my_env/app_2/ch_3/custom/_"
        )


class TestRoundTrip:
    def test_subscribe_filter_matches_published_topic(self) -> None:
        from axonpush.realtime.mqtt import _matches

        published = build_publish_topic(
            ORG_PREFIX,
            app_id="app_2",
            channel_id="ch_3",
            event_type="agent.start",
            agent_id="bot",
            env_slug="prod",
        )
        full_filter = build_subscribe_topic(
            ORG_PREFIX,
            app_id="app_2",
            channel_id="ch_3",
            event_type="agent.start",
            agent_id="bot",
            env_slug="prod",
        )
        wildcard_filter = build_subscribe_topic(ORG_PREFIX, app_id="app_2", channel_id="ch_3")
        assert _matches(full_filter, published)
        assert _matches(wildcard_filter, published)
