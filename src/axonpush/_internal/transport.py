"""HTTP transport layer for the AxonPush SDK.

Builds the generated ``AuthenticatedClient`` with httpx event hooks that:

1. inject auth, tenant, environment and trace headers on every outgoing
   request, and
2. convert non-2xx responses into the SDK's :mod:`axonpush.exceptions`
   hierarchy.

Also exposes synchronous and asynchronous retry helpers that re-issue calls
on :class:`~axonpush.exceptions.RetryableError` with exponential backoff and
honour ``Retry-After`` for rate-limit responses.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Protocol

import httpx

from axonpush._config import Settings
from axonpush._internal.api.client import AuthenticatedClient
from axonpush._tracing import current_trace
from axonpush.exceptions import (
    APIConnectionError,
    AxonPushError,
    RateLimitError,
    RetryableError,
    from_response,
)

_BACKOFF_SCHEDULE: tuple[float, ...] = (0.25, 0.5, 1.0, 2.0, 4.0)


class _DetailedSyncOp(Protocol):
    def sync_detailed(self, **kwargs: Any) -> Any: ...


class _DetailedAsyncOp(Protocol):
    def asyncio_detailed(self, **kwargs: Any) -> Awaitable[Any]: ...


def _auth_headers(settings: Settings) -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if settings.api_key is not None:
        headers["X-API-Key"] = settings.api_key.get_secret_value()
    if settings.tenant_id is not None:
        headers["x-tenant-id"] = settings.tenant_id
    if settings.environment is not None:
        headers["X-Axonpush-Environment"] = settings.environment
    return headers


def _inject_request_headers(request: httpx.Request) -> None:
    ctx = current_trace()
    if ctx is not None:
        request.headers["X-Axonpush-Trace-Id"] = ctx.trace_id


async def _async_inject_request_headers(request: httpx.Request) -> None:
    _inject_request_headers(request)


def _raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    response.read()
    raise from_response(response)


async def _async_raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return
    await response.aread()
    raise from_response(response)


def _base_url_str(settings: Settings) -> str:
    return str(settings.base_url).rstrip("/")


def _make_timeout(settings: Settings) -> httpx.Timeout:
    return httpx.Timeout(settings.timeout, connect=min(5.0, settings.timeout))


def build_sync_client(settings: Settings) -> AuthenticatedClient:
    """Construct an :class:`AuthenticatedClient` for synchronous use.

    Args:
        settings: Effective SDK configuration.

    Returns:
        A generated ``AuthenticatedClient`` whose underlying
        :class:`httpx.Client` has request and response event hooks attached
        for header injection and error mapping.
    """
    headers = _auth_headers(settings)
    base_url = _base_url_str(settings)
    httpx_client = httpx.Client(
        base_url=base_url,
        headers=headers,
        timeout=_make_timeout(settings),
        event_hooks={
            "request": [_inject_request_headers],
            "response": [_raise_for_status],
        },
    )
    client = AuthenticatedClient(
        base_url=base_url,
        token=settings.api_key.get_secret_value() if settings.api_key is not None else "",
        prefix="",
        auth_header_name="X-API-Key",
        raise_on_unexpected_status=False,
        timeout=_make_timeout(settings),
        headers=headers,
    )
    client.set_httpx_client(httpx_client)
    return client


def build_async_client(settings: Settings) -> AuthenticatedClient:
    """Construct an :class:`AuthenticatedClient` for asynchronous use.

    Args:
        settings: Effective SDK configuration.

    Returns:
        A generated ``AuthenticatedClient`` whose underlying
        :class:`httpx.AsyncClient` has the same hooks installed as the sync
        variant.
    """
    headers = _auth_headers(settings)
    base_url = _base_url_str(settings)
    httpx_client = httpx.AsyncClient(
        base_url=base_url,
        headers=headers,
        timeout=_make_timeout(settings),
        event_hooks={
            "request": [_async_inject_request_headers],
            "response": [_async_raise_for_status],
        },
    )
    client = AuthenticatedClient(
        base_url=base_url,
        token=settings.api_key.get_secret_value() if settings.api_key is not None else "",
        prefix="",
        auth_header_name="X-API-Key",
        raise_on_unexpected_status=False,
        timeout=_make_timeout(settings),
        headers=headers,
    )
    client.set_async_httpx_client(httpx_client)
    return client


def _backoff_for(attempt: int, error: AxonPushError) -> float:
    if isinstance(error, RateLimitError) and error.retry_after is not None:
        return max(0.0, float(error.retry_after))
    idx = min(attempt, len(_BACKOFF_SCHEDULE) - 1)
    return _BACKOFF_SCHEDULE[idx]


def _wrap_transport_error(exc: BaseException) -> APIConnectionError:
    return APIConnectionError(f"Failed to connect to AxonPush API: {exc}")


def call_with_retries_sync(
    op: _DetailedSyncOp | Any,
    *,
    max_retries: int,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> Any:
    """Invoke ``op.sync_detailed(**kwargs)`` with exponential-backoff retries.

    Retries on any :class:`~axonpush.exceptions.RetryableError`. Network
    failures from httpx are mapped to
    :class:`~axonpush.exceptions.APIConnectionError` (which is retryable).
    Non-retryable errors are re-raised on the first attempt.

    Args:
        op: The generated operation module (must expose ``sync_detailed``).
        max_retries: Number of additional attempts after the initial call.
            ``0`` disables retries entirely.
        sleep: Override for the sleep function. Tests pass a fake.
        **kwargs: Forwarded to ``op.sync_detailed``.

    Returns:
        The :class:`Response` object returned by the operation.

    Raises:
        AxonPushError: The mapped SDK error if every attempt fails.
    """
    last_error: AxonPushError | None = None
    for attempt in range(max_retries + 1):
        try:
            return op.sync_detailed(**kwargs)
        except RetryableError as exc:
            last_error = exc
        except (httpx.TransportError, httpx.RequestError) as exc:
            last_error = _wrap_transport_error(exc)
        except AxonPushError:
            raise
        if attempt < max_retries:
            sleep(_backoff_for(attempt, last_error))
            continue
        break
    assert last_error is not None
    raise last_error


async def call_with_retries_async(
    op: _DetailedAsyncOp | Any,
    *,
    max_retries: int,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    **kwargs: Any,
) -> Any:
    """Async sibling of :func:`call_with_retries_sync`.

    Args:
        op: The generated operation module (must expose ``asyncio_detailed``).
        max_retries: Number of additional attempts after the initial call.
        sleep: Override for the async sleep function. Tests pass a fake.
        **kwargs: Forwarded to ``op.asyncio_detailed``.

    Returns:
        The :class:`Response` object returned by the operation.

    Raises:
        AxonPushError: The mapped SDK error if every attempt fails.
    """
    last_error: AxonPushError | None = None
    for attempt in range(max_retries + 1):
        try:
            return await op.asyncio_detailed(**kwargs)
        except RetryableError as exc:
            last_error = exc
        except (httpx.TransportError, httpx.RequestError) as exc:
            last_error = _wrap_transport_error(exc)
        except AxonPushError:
            raise
        if attempt < max_retries:
            await sleep(_backoff_for(attempt, last_error))
            continue
        break
    assert last_error is not None
    raise last_error


__all__ = [
    "build_async_client",
    "build_sync_client",
    "call_with_retries_async",
    "call_with_retries_sync",
]
