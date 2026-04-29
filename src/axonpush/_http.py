from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from axonpush._auth import AuthConfig
from axonpush.exceptions import (
    APIConnectionError,
    AuthenticationError,
    AxonPushError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

logger = logging.getLogger("axonpush")

_DEFAULT_POOL_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=20,
    keepalive_expiry=30.0,
)

_FAIL_OPEN_SENTINEL = object()


def _is_fail_open(result: Any) -> bool:
    return result is _FAIL_OPEN_SENTINEL


_ERROR_MAP: Dict[int, type] = {
    400: ValidationError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    429: RateLimitError,
}


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return

    status = response.status_code
    try:
        body = response.json()
        message = body.get("message", response.text)
        if isinstance(message, list):
            message = "; ".join(str(m) for m in message)
    except Exception:
        message = response.text or f"HTTP {status}"

    if status == 429:
        retry_after_raw = response.headers.get("Retry-After")
        retry_after = float(retry_after_raw) if retry_after_raw else None
        raise RateLimitError(str(message), retry_after=retry_after)

    exc_cls = _ERROR_MAP.get(status)
    if exc_cls is not None:
        raise exc_cls(str(message), status_code=status)

    if status >= 500:
        raise ServerError(str(message), status_code=status)

    raise AxonPushError(str(message), status_code=status)


class SyncTransport:
    """Synchronous HTTP transport backed by httpx.Client."""

    def __init__(self, auth: AuthConfig, timeout: float = 30.0, *, fail_open: bool = True) -> None:
        self._auth = auth
        self._fail_open = fail_open
        self._client = httpx.Client(
            base_url=auth.base_url,
            headers=auth.headers(),
            timeout=httpx.Timeout(timeout, connect=5.0),
            limits=_DEFAULT_POOL_LIMITS,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = self._client.request(method, path, json=json, params=params)
        except httpx.TransportError as exc:
            if self._fail_open:
                logger.warning(
                    "AxonPush API request failed (%s %s): %s. "
                    "The error was suppressed (fail_open=True).",
                    method, path, exc,
                )
                return _FAIL_OPEN_SENTINEL
            raise APIConnectionError(
                f"Failed to connect to AxonPush API: {exc}",
            ) from exc
        _raise_for_status(response)
        if not response.content:
            return None
        return response.json()

    def close(self) -> None:
        self._client.close()


class AsyncTransport:
    """Asynchronous HTTP transport backed by httpx.AsyncClient."""

    def __init__(self, auth: AuthConfig, timeout: float = 30.0, *, fail_open: bool = True) -> None:
        self._auth = auth
        self._fail_open = fail_open
        self._client = httpx.AsyncClient(
            base_url=auth.base_url,
            headers=auth.headers(),
            timeout=httpx.Timeout(timeout, connect=5.0),
            limits=_DEFAULT_POOL_LIMITS,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        try:
            response = await self._client.request(method, path, json=json, params=params)
        except httpx.TransportError as exc:
            if self._fail_open:
                logger.warning(
                    "AxonPush API request failed (%s %s): %s. "
                    "The error was suppressed (fail_open=True).",
                    method, path, exc,
                )
                return _FAIL_OPEN_SENTINEL
            raise APIConnectionError(
                f"Failed to connect to AxonPush API: {exc}",
            ) from exc
        _raise_for_status(response)
        if not response.content:
            return None
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
