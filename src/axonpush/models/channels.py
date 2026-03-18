from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateChannelParams(BaseModel):
    name: str
    app_id: int = Field(alias="appId")

    model_config = {"populate_by_name": True}


class Channel(BaseModel):
    id: int
    name: str
    app: Optional[dict] = None  # noqa: UP007 — simplified; nested App object

    model_config = {"populate_by_name": True}
