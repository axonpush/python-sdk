"""HTTP error → exception mapping. Verifies axonpush/_http.py:_raise_for_status
and the fail-open behavior of SyncTransport / AsyncTransport.

These tests pin the exception contract that downstream code (and the user)
relies on. If you change the mapping, update both the test and any caller
that catches a specific subclass.
"""
from __future__ import annotations

import httpx
import pytest

from axonpush import AsyncAxonPush, AxonPush
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

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


@pytest.mark.parametrize(
    ("status", "exc_class"),
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (500, ServerError),
        (502, ServerError),
        (503, ServerError),
    ],
)
def test_status_code_maps_to_exception(mock_router, status, exc_class):
    mock_router.post("/event").mock(
        return_value=httpx.Response(status, json={"message": "boom"})
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(exc_class) as exc_info:
            c.events.publish("x", {}, channel_id=1)
        assert exc_info.value.status_code == status
        assert "boom" in str(exc_info.value)


def test_429_raises_rate_limit_with_retry_after(mock_router):
    mock_router.post("/event").mock(
        return_value=httpx.Response(
            429,
            json={"message": "slow down"},
            headers={"Retry-After": "12"},
        )
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(RateLimitError) as exc_info:
            c.events.publish("x", {}, channel_id=1)
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 12.0


def test_429_without_retry_after_header(mock_router):
    mock_router.post("/event").mock(
        return_value=httpx.Response(429, json={"message": "slow down"})
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(RateLimitError) as exc_info:
            c.events.publish("x", {}, channel_id=1)
        assert exc_info.value.retry_after is None


def test_unknown_4xx_raises_base_error(mock_router):
    mock_router.post("/event").mock(
        return_value=httpx.Response(418, json={"message": "i am a teapot"})
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(AxonPushError) as exc_info:
            c.events.publish("x", {}, channel_id=1)
        assert exc_info.value.status_code == 418


def test_validation_error_message_list_is_joined(mock_router):
    """NestJS class-validator returns `message` as a list of strings."""
    mock_router.post("/event").mock(
        return_value=httpx.Response(
            400,
            json={"message": ["identifier should not be empty", "channel_id must be int"]},
        )
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        with pytest.raises(ValidationError) as exc_info:
            c.events.publish("", {}, channel_id=1)
        msg = str(exc_info.value)
        assert "identifier should not be empty" in msg
        assert "channel_id must be int" in msg


def test_fail_open_swallows_connection_error(mock_router, caplog):
    """With fail_open=True (default), TransportError → returns None, logs warning."""
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("refused"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
    ) as c:
        result = c.events.publish("x", {}, channel_id=1)
    assert result is None  # publish() converts the fail-open sentinel to None


def test_fail_closed_raises_api_connection_error(mock_router):
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("refused"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=False
    ) as c:
        with pytest.raises(APIConnectionError):
            c.events.publish("x", {}, channel_id=1)


async def test_async_status_mapping(mock_router):
    mock_router.post("/event").mock(
        return_value=httpx.Response(401, json={"message": "no creds"})
    )
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as c:
        with pytest.raises(AuthenticationError):
            await c.events.publish("x", {}, channel_id=1)


async def test_async_fail_open(mock_router):
    mock_router.post("/event").mock(side_effect=httpx.ConnectError("refused"))
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
    ) as c:
        result = await c.events.publish("x", {}, channel_id=1)
    assert result is None
