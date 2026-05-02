"""MQTT topic builders.

Wire format pinned by the backend at
``easy-push/src/pubsub/topic-builder.ts``::

    {topic_prefix}/{env_slug}/{app_id}/{channel_id}/{event_type}/{agent_id}

``topic_prefix`` is org-scoped (``axonpush/{org_id}``) and is returned by
the ``/auth/iot-credentials`` endpoint as ``topicPrefix`` — callers should
forward it verbatim. Each segment is sanitised with
``[^a-zA-Z0-9_-] -> _`` to satisfy AWS IoT topic-name rules. On publish,
a missing ``env_slug`` falls back to the default env slug returned with
the credentials response (typically ``"default"``); other missing
segments fall back to ``_``. On subscribe, every missing slot becomes the
MQTT ``+`` wildcard.
"""

from __future__ import annotations

import re

_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")
_FALLBACK_ENV_SLUG = "default"


def _sanitize(value: str) -> str:
    cleaned = _SAFE_RE.sub("_", value)
    return cleaned or "_"


def _publish_segment(value: str | None) -> str:
    if value is None or value == "":
        return "_"
    return _sanitize(value)


def _subscribe_segment(value: str | None) -> str:
    if value is None or value == "":
        return "+"
    return _sanitize(value)


def build_publish_topic(
    topic_prefix: str,
    *,
    app_id: str,
    channel_id: str,
    event_type: str,
    agent_id: str | None = None,
    env_slug: str | None = None,
    default_env_slug: str = _FALLBACK_ENV_SLUG,
) -> str:
    """Build the MQTT topic the backend publishes events to.

    Args:
        topic_prefix: Org-scoped prefix from the credentials response
            (``IotCredentials.topic_prefix``). Used verbatim — already
            sanitised by the backend.
        app_id: App ID (UUID string).
        channel_id: Channel ID (UUID string).
        event_type: Event type (e.g. ``"agent.start"`` or ``"custom"``).
        agent_id: Optional agent ID.
        env_slug: Environment slug. If ``None`` or empty, falls back to
            ``default_env_slug``.
        default_env_slug: Slug used when ``env_slug`` is missing —
            defaults to ``"default"`` to match the backend.

    Returns:
        The fully-qualified MQTT topic string.
    """
    env = env_slug if env_slug else default_env_slug
    return "/".join(
        (
            topic_prefix,
            _sanitize(env),
            _sanitize(app_id),
            _sanitize(channel_id),
            _sanitize(event_type),
            _publish_segment(agent_id),
        )
    )


def build_subscribe_topic(
    topic_prefix: str,
    *,
    app_id: str | None = None,
    channel_id: str | None = None,
    event_type: str | None = None,
    agent_id: str | None = None,
    env_slug: str | None = None,
) -> str:
    """Build an MQTT topic filter for ``subscribe``.

    Missing segments collapse to the MQTT ``+`` single-level wildcard.

    Args:
        topic_prefix: Org-scoped prefix from the credentials response.
        app_id: App ID, or ``None`` for any.
        channel_id: Channel ID, or ``None`` for any.
        event_type: Event type, or ``None`` for any.
        agent_id: Agent ID, or ``None`` for any.
        env_slug: Environment slug, or ``None`` for any.

    Returns:
        The MQTT topic-filter string.
    """
    return "/".join(
        (
            topic_prefix,
            _subscribe_segment(env_slug),
            _subscribe_segment(app_id),
            _subscribe_segment(channel_id),
            _subscribe_segment(event_type),
            _subscribe_segment(agent_id),
        )
    )
