from __future__ import annotations


class AuthConfig:
    """Immutable auth configuration. Thread-safe (read-only after construction)."""

    __slots__ = ("api_key", "tenant_id", "base_url", "environment")

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        base_url: str,
        environment: str | None = None,
    ) -> None:
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.base_url = base_url.rstrip("/")
        self.environment = environment

    def headers(self) -> dict[str, str]:
        h = {
            "X-API-Key": self.api_key,
            "x-tenant-id": self.tenant_id,
            "Content-Type": "application/json",
        }
        if self.environment:
            h["X-Axonpush-Environment"] = self.environment
        return h
