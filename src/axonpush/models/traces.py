from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from axonpush.models.events import Event


class TraceListItem(BaseModel):
    trace_id: str = Field(alias="traceId")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    event_count: int = Field(alias="eventCount")

    model_config = {"populate_by_name": True}


class TraceSummary(BaseModel):
    trace_id: str = Field(alias="traceId")
    total_events: int = Field(alias="totalEvents")
    agents: List[str]
    event_types: List[str] = Field(alias="eventTypes")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    duration_ms: int = Field(alias="durationMs")
    error_count: int = Field(alias="errorCount")
    tool_call_count: int = Field(alias="toolCallCount")
    handoff_count: int = Field(alias="handoffCount")
    events: List[Event]

    model_config = {"populate_by_name": True}
