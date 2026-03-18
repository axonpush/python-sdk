from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Generator, Iterator, Optional

import httpx
from httpx_sse import EventSource, connect_sse, aconnect_sse

from axonpush._auth import AuthConfig
from axonpush.exceptions import (
    AuthenticationError,
    AxonPushError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

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

    def __init__(self, auth: AuthConfig, timeout: float = 30.0) -> None:
        self._auth = auth
        self._client = httpx.Client(
            base_url=auth.base_url,
            headers=auth.headers(),
            timeout=timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        response = self._client.request(method, path, json=json, params=params)
        _raise_for_status(response)
        if not response.content:
            return None
        return response.json()

    @contextmanager
    def stream_sse(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Generator[EventSource, None, None]:
        with connect_sse(
            self._client, "GET", path, params=params or {}
        ) as event_source:
            yield event_source

    def close(self) -> None:
        self._client.close()


class AsyncTransport:
    """Asynchronous HTTP transport backed by httpx.AsyncClient."""

    def __init__(self, auth: AuthConfig, timeout: float = 30.0) -> None:
        self._auth = auth
        self._client = httpx.AsyncClient(
            base_url=auth.base_url,
            headers=auth.headers(),
            timeout=timeout,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        response = await self._client.request(method, path, json=json, params=params)
        _raise_for_status(response)
        if not response.content:
            return None
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
