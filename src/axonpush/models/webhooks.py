from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class CreateWebhookEndpointParams(BaseModel):
    url: str
    channel_id: int = Field(alias="channelId")
    secret: Optional[str] = None
    event_types: Optional[List[str]] = Field(None, alias="eventTypes")
    description: Optional[str] = None

    model_config = {"populate_by_name": True}


class WebhookEndpoint(BaseModel):
    id: int
    url: str
    channel_id: int = Field(alias="channelId")
    event_types: Optional[List[str]] = Field(None, alias="eventTypes")
    active: bool = True
    description: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    model_config = {"populate_by_name": True}


class WebhookDelivery(BaseModel):
    id: int
    endpoint_id: int = Field(alias="endpointId")
    event_id: int = Field(alias="eventId")
    status: DeliveryStatus
    attempts: int = 0
    status_code: Optional[int] = Field(None, alias="statusCode")
    response_body: Optional[str] = Field(None, alias="responseBody")
    error: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")

    model_config = {"populate_by_name": True}
