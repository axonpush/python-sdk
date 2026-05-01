from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateEnvironmentParams(BaseModel):
    name: str
    slug: Optional[str] = None
    color: Optional[str] = None
    is_production: Optional[bool] = Field(default=None, alias="isProduction")
    is_default: Optional[bool] = Field(default=None, alias="isDefault")
    clone_from_env_id: Optional[str] = Field(default=None, alias="cloneFromEnvId")

    model_config = {"populate_by_name": True}


class UpdateEnvironmentParams(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    color: Optional[str] = None
    is_production: Optional[bool] = Field(default=None, alias="isProduction")
    is_default: Optional[bool] = Field(default=None, alias="isDefault")

    model_config = {"populate_by_name": True}


class Environment(BaseModel):
    id: str
    environment_id: str = Field(alias="environmentId")
    org_id: str = Field(alias="orgId")
    name: str
    slug: str
    color: Optional[str] = None
    is_default: Optional[bool] = Field(default=None, alias="isDefault")
    is_production: Optional[bool] = Field(default=None, alias="isProduction")
    is_ephemeral: Optional[bool] = Field(default=None, alias="isEphemeral")
    expires_at: Optional[datetime] = Field(default=None, alias="expiresAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    deleted_at: Optional[datetime] = Field(default=None, alias="deletedAt")

    model_config = {"populate_by_name": True}
