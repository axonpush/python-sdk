from __future__ import annotations

from typing import Optional, Union

from axonpush.models.events import EventType


def _slot(value: Optional[Union[str, EventType]]) -> str:
    if value is None:
        return "+"
    if isinstance(value, EventType):
        return value.value
    return value


def build_subscribe_topic(
    org_id: str,
    app_id: str,
    channel_id: str,
    event_type: Optional[Union[str, EventType]] = None,
    agent_id: Optional[str] = None,
) -> str:
    return (
        f"axonpush/{org_id}/{app_id}/{channel_id}/"
        f"{_slot(event_type)}/{_slot(agent_id)}"
    )


def build_publish_topic(
    org_id: str,
    app_id: str,
    channel_id: str,
    event_type: Union[str, EventType],
    agent_id: Optional[str] = None,
) -> str:
    return (
        f"axonpush/{org_id}/{app_id}/{channel_id}/"
        f"{_slot(event_type)}/{_slot(agent_id)}"
    )
