from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class TraceListItem(BaseModel):
    trace_id: str = Field(alias="traceId")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    event_count: int = Field(alias="eventCount")
    error_count: int = Field(0, alias="errorCount")
    tool_call_count: int = Field(0, alias="toolCallCount")
    handoff_count: int = Field(0, alias="handoffCount")
    agents: List[str] = Field(default_factory=list)
    duration: int = Field(0)

    model_config = {"populate_by_name": True}


class TraceSummary(BaseModel):
    trace_id: str = Field(alias="traceId")
    event_count: int = Field(alias="eventCount")
    agents: List[str]
    event_types: List[str] = Field(alias="eventTypes")
    start_time: datetime = Field(alias="startTime")
    end_time: datetime = Field(alias="endTime")
    duration_ms: int = Field(alias="duration")
    error_count: int = Field(alias="errorCount")
    tool_call_count: int = Field(alias="toolCallCount")
    handoff_count: int = Field(alias="handoffCount")

    model_config = {"populate_by_name": True}
