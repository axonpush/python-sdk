"""Credential-fetch helper tests — mocks the /auth/iot-credentials endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from axonpush import AsyncAxonPush, AxonPush
from axonpush.realtime.credentials import (
    fetch_credentials_async,
    fetch_credentials_sync,
)

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _credential_payload(expires_in_seconds: int = 3600) -> dict:
    return {
        "endpoint": "abc-ats.iot.us-east-1.amazonaws.com",
        "presignedWssUrl": "wss://abc-ats.iot.us-east-1.amazonaws.com/mqtt?X-Amz=token",
        "expiresAt": (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        ).isoformat(),
    }


def test_sync_fetch_parses_payload(mock_router):
    mock_router.get("/auth/iot-credentials").mock(
        return_value=httpx.Response(200, json=_credential_payload())
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        creds = fetch_credentials_sync(c._transport)
    assert creds is not None
    assert creds.endpoint.endswith(".amazonaws.com")
    assert creds.presigned_wss_url.startswith("wss://")
    assert creds.expires_in() > 3500


def test_sync_fetch_sends_endpoint_param(mock_router):
    route = mock_router.get("/auth/iot-credentials").mock(
        return_value=httpx.Response(200, json=_credential_payload())
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        fetch_credentials_sync(c._transport, iot_endpoint="custom.iot")
    assert route.calls.last.request.url.params.get("endpoint") == "custom.iot"


def test_sync_fetch_returns_none_on_fail_open(mock_router):
    mock_router.get("/auth/iot-credentials").mock(side_effect=httpx.ConnectError("nope"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
    ) as c:
        creds = fetch_credentials_sync(c._transport)
    assert creds is None


def test_sync_fetch_handles_missing_keys(mock_router):
    mock_router.get("/auth/iot-credentials").mock(
        return_value=httpx.Response(200, json={"endpoint": "x"}),
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        creds = fetch_credentials_sync(c._transport)
    assert creds is None


def test_sync_fetch_parses_z_suffix(mock_router):
    payload = _credential_payload()
    payload["expiresAt"] = "2099-01-01T00:00:00Z"
    mock_router.get("/auth/iot-credentials").mock(
        return_value=httpx.Response(200, json=payload),
    )
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        creds = fetch_credentials_sync(c._transport)
    assert creds is not None
    assert creds.expires_at.year == 2099
    assert creds.expires_at.tzinfo is not None


@pytest.mark.asyncio
async def test_async_fetch_parses_payload(mock_router):
    mock_router.get("/auth/iot-credentials").mock(
        return_value=httpx.Response(200, json=_credential_payload())
    )
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as c:
        creds = await fetch_credentials_async(c._transport)
    assert creds is not None
    assert creds.expires_in() > 3500
