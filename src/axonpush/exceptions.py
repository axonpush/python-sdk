from __future__ import annotations


class AxonPushError(Exception):
    """Base exception for all AxonPush SDK errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AxonPushError):
    """Raised when the API key or JWT token is invalid or missing (HTTP 401)."""


class ForbiddenError(AxonPushError):
    """Raised when the authenticated user lacks permission (HTTP 403)."""


class NotFoundError(AxonPushError):
    """Raised when the requested resource does not exist (HTTP 404)."""


class ValidationError(AxonPushError):
    """Raised when the request body fails validation (HTTP 400)."""


class RateLimitError(AxonPushError):
    """Raised when the rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class ServerError(AxonPushError):
    """Raised when the server returns a 5xx error."""
