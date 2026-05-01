from __future__ import annotations

import re
from typing import Optional, Union

from axonpush.models.events import EventType

_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")
_DEFAULT_ENV_SLUG = "default"


def _safe_segment(value: Optional[Union[str, int, EventType]]) -> str:
    if value is None or value == "":
        return "_"
    if isinstance(value, EventType):
        value = value.value
    if value == "+" or value == "#":
        return str(value)
    sanitized = _SAFE_RE.sub("_", str(value))
    return sanitized or "_"


def _slot(value: Optional[Union[str, int, EventType]]) -> str:
    if value is None or value == "":
        return "+"
    return _safe_segment(value)


def _env_publish_segment(env: Optional[str]) -> str:
    if env is None or env == "":
        return _DEFAULT_ENV_SLUG
    return _safe_segment(env)


def build_subscribe_topic(
    org_id: str,
    app_id: Optional[str] = None,
    channel_id: Optional[Union[int, str]] = None,
    event_type: Optional[Union[str, EventType]] = None,
    agent_id: Optional[str] = None,
    *,
    environment: Optional[str] = None,
) -> str:
    return (
        f"axonpush/{_safe_segment(org_id)}/{_slot(environment)}/"
        f"{_slot(app_id)}/{_slot(channel_id)}/"
        f"{_slot(event_type)}/{_slot(agent_id)}"
    )


def build_publish_topic(
    org_id: str,
    app_id: str,
    channel_id: Union[int, str],
    event_type: Union[str, EventType],
    agent_id: Optional[str] = None,
    *,
    environment: Optional[str] = None,
) -> str:
    return (
        f"axonpush/{_safe_segment(org_id)}/{_env_publish_segment(environment)}/"
        f"{_safe_segment(app_id)}/{_safe_segment(channel_id)}/"
        f"{_safe_segment(event_type)}/{_safe_segment(agent_id)}"
    )
