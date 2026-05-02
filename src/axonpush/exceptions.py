"""Exception hierarchy for the AxonPush SDK.

Every exception raised by the SDK derives from :class:`AxonPushError`. Each
carries the request id, status code, error code and operator hint emitted by
the backend's global exception filter (response shape:
``{ "code": str, "message": str, "hint": str | None, "requestId": str | None }``).

The :class:`RetryableError` mixin marks subclasses that the transport retry
helper should automatically retry with exponential backoff.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

    from axonpush._internal.api.errors import UnexpectedStatus


class AxonPushError(Exception):
    """Base exception for every error raised by the AxonPush SDK.

    Args:
        message: Human-readable description of the failure.
        status_code: HTTP status returned by the backend, when applicable.
        code: Stable machine-readable error code from the backend payload.
        hint: Optional remediation hint surfaced by the backend.
        request_id: Backend-issued request identifier (``X-Request-Id``).
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        hint: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.hint = hint
        self.request_id = request_id


class RetryableError(AxonPushError):
    """Mixin marking errors that the transport may safely retry.

    Subclasses should be retried with exponential backoff. The retry helper
    reads :attr:`RateLimitError.retry_after` to honour ``Retry-After``.
    """


class APIConnectionError(RetryableError):
    """Raised when the SDK cannot reach the AxonPush API.

    Covers DNS failures, connection refused, read timeouts and similar
    transport-layer faults. The facade swallows this when ``fail_open=True``.
    """


class AuthenticationError(AxonPushError):
    """Raised on HTTP 401 responses (missing or invalid credentials)."""


class ForbiddenError(AxonPushError):
    """Raised on HTTP 403 responses (authenticated but not permitted)."""


class NotFoundError(AxonPushError):
    """Raised on HTTP 404 responses (resource does not exist)."""


class ValidationError(AxonPushError):
    """Raised when the backend rejects a request body.

    Maps to HTTP 422 or to any 4xx response whose payload reports
    ``code: "validation_error"``.
    """


class RateLimitError(RetryableError):
    """Raised on HTTP 429 responses.

    Args:
        message: Human-readable description of the failure.
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` response header. ``None`` when not provided.
        status_code: Always 429 for this error; accepted for parity.
        code: Stable machine-readable error code.
        hint: Optional remediation hint.
        request_id: Backend-issued request identifier.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        status_code: int | None = 429,
        code: str | None = None,
        hint: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            code=code,
            hint=hint,
            request_id=request_id,
        )
        self.retry_after = retry_after


class ServerError(RetryableError):
    """Raised on HTTP 5xx responses."""


def _safe_json(response: Any) -> dict[str, Any] | None:
    try:
        body = response.json()
    except Exception:
        return None
    if isinstance(body, dict):
        return body
    return None


def _parse_retry_after(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def from_response(
    response: "httpx.Response | UnexpectedStatus",
    body: dict[str, Any] | None = None,
) -> AxonPushError:
    """Build the right :class:`AxonPushError` subclass from a backend response.

    Accepts either a raw :class:`httpx.Response` or the generated client's
    :class:`~axonpush._internal.api.errors.UnexpectedStatus` and parses the
    standard ``{ code, message, hint, requestId }`` envelope.

    Args:
        response: The HTTP response (or wrapped ``UnexpectedStatus``) that
            triggered the error.
        body: Optional pre-parsed JSON body. When omitted, the body is read
            from ``response`` directly.

    Returns:
        An :class:`AxonPushError` subclass matching the status code and code
        emitted by the backend.
    """
    from axonpush._internal.api.errors import UnexpectedStatus

    status_code: int | None
    headers: dict[str, str] = {}
    parsed_body: dict[str, Any] | None = body

    if isinstance(response, UnexpectedStatus):
        status_code = int(response.status_code)
        if parsed_body is None:
            import json

            try:
                decoded = json.loads(response.content.decode("utf-8", errors="ignore"))
            except Exception:
                decoded = None
            if isinstance(decoded, dict):
                parsed_body = decoded
    else:
        status_code = int(response.status_code)
        headers = {k.lower(): v for k, v in response.headers.items()}
        if parsed_body is None:
            parsed_body = _safe_json(response)

    parsed_body = parsed_body or {}
    raw_code = parsed_body.get("code")
    code = raw_code if isinstance(raw_code, str) else None
    message_raw = parsed_body.get("message")
    if isinstance(message_raw, list):
        message = "; ".join(str(m) for m in message_raw)
    elif isinstance(message_raw, str):
        message = message_raw
    else:
        message = f"HTTP {status_code}"
    raw_hint = parsed_body.get("hint")
    hint = raw_hint if isinstance(raw_hint, str) else None
    raw_request_id = parsed_body.get("requestId")
    request_id = (
        raw_request_id if isinstance(raw_request_id, str) else headers.get("x-request-id")
    )

    common: dict[str, Any] = {
        "status_code": status_code,
        "code": code,
        "hint": hint,
        "request_id": request_id,
    }

    if status_code == 401:
        return AuthenticationError(message, **common)
    if status_code == 403:
        return ForbiddenError(message, **common)
    if status_code == 404:
        return NotFoundError(message, **common)
    if status_code == 422 or code == "validation_error":
        return ValidationError(message, **common)
    if status_code == 429:
        retry_after = _parse_retry_after(headers.get("retry-after"))
        return RateLimitError(message, retry_after=retry_after, **common)
    if status_code is not None and status_code >= 500:
        return ServerError(message, **common)
    return AxonPushError(message, **common)


__all__ = [
    "APIConnectionError",
    "AuthenticationError",
    "AxonPushError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "RetryableError",
    "ServerError",
    "ValidationError",
    "from_response",
]
