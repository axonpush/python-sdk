from __future__ import annotations

from pydantic import BaseModel


class PaginatedParams(BaseModel):
    page: int = 1
    limit: int = 10
