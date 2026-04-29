from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from axonpush.models.events import EventType


class EventQuery(BaseModel):
    """Typed query parameters for ``GET /event``.

    Mirrors the backend's Zod schema. All fields optional; the server picks
    the optimal access pattern based on which fields are present.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    channel_id: Optional[str] = Field(default=None, alias="channelId")
    app_id: Optional[str] = Field(default=None, alias="appId")
    environment_id: Optional[str] = Field(default=None, alias="environmentId")
    event_type: Optional[Union[EventType, str, List[Union[EventType, str]]]] = Field(
        default=None, alias="eventType"
    )
    agent_id: Optional[str] = Field(default=None, alias="agentId")
    trace_id: Optional[str] = Field(default=None, alias="traceId")
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    cursor: Optional[str] = None
    limit: Optional[int] = Field(default=None, ge=1, le=1000)
    payload_filter: Optional[Dict[str, Any]] = Field(default=None, alias="payloadFilter")

    @field_validator("event_type")
    @classmethod
    def _normalise_event_type(
        cls,
        value: Optional[Union[EventType, str, List[Union[EventType, str]]]],
    ) -> Optional[Union[str, List[str]]]:
        if value is None:
            return None
        if isinstance(value, list):
            return [v.value if isinstance(v, EventType) else str(v) for v in value]
        if isinstance(value, EventType):
            return value.value
        return str(value)

    def to_query_params(self) -> Dict[str, Any]:
        import json as _json

        params: Dict[str, Any] = {}
        data = self.model_dump(by_alias=True, exclude_none=True)
        for key, value in data.items():
            if key == "payloadFilter":
                params[key] = _json.dumps(value)
                continue
            if key == "since" or key == "until":
                params[key] = (
                    value.isoformat() if isinstance(value, datetime) else value
                )
                continue
            if isinstance(value, list):
                params[key] = ",".join(str(v) for v in value)
                continue
            params[key] = value
        return params


class EventListResult(BaseModel):
    data: List[Any] = Field(default_factory=list)
    cursor: Optional[str] = None
