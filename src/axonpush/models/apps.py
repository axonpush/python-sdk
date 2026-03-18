from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CreateAppParams(BaseModel):
    name: str


class App(BaseModel):
    id: int
    name: str
    creator: Optional[Dict[str, Any]] = None
    organization_id: Optional[int] = Field(None, alias="organizationId")
    channels: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
