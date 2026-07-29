"""Settings model for the AxonPush SDK.

Wraps configuration into a frozen pydantic v2 model that reads defaults from
environment variables (``AXONPUSH_*``). Constructor kwargs override env vars.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ContentCaptureMode = Literal["metadata_only", "redacted", "full"]


class Settings(BaseSettings):
    """Effective configuration for an :class:`~axonpush.client.AxonPush` client.

    Fields default to the matching ``AXONPUSH_*`` environment variable when
    one is set, otherwise to the values shown below. Constructor kwargs win
    over environment variables.

    Attributes:
        api_key: API key (``AXONPUSH_API_KEY``). Wrapped in
            :class:`~pydantic.SecretStr` so it never appears in
            ``repr()`` output.
        tenant_id: Tenant / organisation id (``AXONPUSH_TENANT_ID``).
        base_url: Backend base URL (``AXONPUSH_BASE_URL``). Defaults to
            ``http://localhost:3000``.
        environment: Logical environment name, propagated as
            ``X-Axonpush-Environment`` (``AXONPUSH_ENVIRONMENT``).
        timeout: Per-request timeout in seconds (``AXONPUSH_TIMEOUT``).
        max_retries: Maximum number of automatic retries for retryable
            failures (``AXONPUSH_MAX_RETRIES``).
        fail_open: When true (the default), the facade swallows
            :class:`~axonpush.exceptions.APIConnectionError` and returns
            ``None`` from invocations, so observability never crashes the
            host application. Set ``False`` (``AXONPUSH_FAIL_OPEN=false``)
            to surface connection errors instead.
    """

    api_key: SecretStr | None = None
    tenant_id: str | None = None
    base_url: HttpUrl = HttpUrl("http://localhost:3000")
    environment: str | None = None
    timeout: float = 30.0
    max_retries: int = 3
    fail_open: bool = True
    content_capture_mode: ContentCaptureMode = "metadata_only"
    redact_keys: Annotated[list[str], NoDecode] = Field(default_factory=list)
    max_content_length: int = Field(default=4096, ge=1)

    @field_validator("redact_keys", mode="before")
    @classmethod
    def _parse_redact_keys(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(
        env_prefix="AXONPUSH_",
        frozen=True,
        extra="ignore",
        case_sensitive=False,
    )


__all__ = ["ContentCaptureMode", "Settings"]
