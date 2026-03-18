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

    model_config = {"populate_by_name": True}


class Event(BaseModel):
    id: int
    identifier: str
    payload: Dict[str, Any]
    agent_id: Optional[str] = Field(None, alias="agentId")
    trace_id: Optional[str] = Field(None, alias="traceId")
    span_id: Optional[str] = Field(None, alias="spanId")
    parent_event_id: Optional[int] = Field(None, alias="parentEventId")
    event_type: EventType = Field(alias="eventType", default=EventType.CUSTOM)
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}
