from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_MESSAGE = "agent.message"
    AGENT_TOOL_CALL_START = "agent.tool_call.start"
    AGENT_TOOL_CALL_END = "agent.tool_call.end"
    AGENT_ERROR = "agent.error"
    AGENT_HANDOFF = "agent.handoff"
    AGENT_LLM_TOKEN = "agent.llm.token"
    AGENT_LOG = "agent.log"
    APP_LOG = "app.log"
    APP_SPAN = "app.span"
    CUSTOM = "custom"


class CreateEventParams(BaseModel):
    identifier: str
    payload: Dict[str, Any]
    channel_id: int
    agent_id: Optional[str] = Field(None, alias="agentId")
    trace_id: Optional[str] = Field(None, alias="traceId")
    span_id: Optional[str] = Field(None, alias="spanId")
    parent_event_id: Optional[int] = Field(None, alias="parentEventId")
    event_type: Optional[EventType] = Field(None, alias="eventType")
    metadata: Optional[Dict[str, Any]] = None
    environment: Optional[str] = None
    # Force the server's synchronous write path for this call. The default
    # async path returns in under a millisecond but the response won't carry
    # a DB-assigned `id`. Use sync=True for audit-critical writes.
    sync: Optional[bool] = None

    model_config = {"populate_by_name": True}


class Event(BaseModel):
    # `id` is absent when the server's async_ingest flag is on — the response
    # shape is `{identifier, queued: true, createdAt, environmentId}`.
    id: Optional[int] = None
    queued: Optional[bool] = None
    identifier: str
    payload: Optional[Dict[str, Any]] = None
    agent_id: Optional[str] = Field(None, alias="agentId")
    trace_id: Optional[str] = Field(None, alias="traceId")
    span_id: Optional[str] = Field(None, alias="spanId")
    parent_event_id: Optional[int] = Field(None, alias="parentEventId")
    event_type: EventType = Field(alias="eventType", default=EventType.CUSTOM)
    metadata: Optional[Dict[str, Any]] = None
    environment_id: Optional[int] = Field(None, alias="environmentId")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = {"populate_by_name": True}
