"""Credential helper tests — mock the generated op via the fake facade."""

from __future__ import annotations

import pytest

from axonpush._internal.api.api.auth import (
    iot_credentials_controller_get_credentials as _gen,
)
from axonpush.realtime.credentials import (
    IotCredentials,
    fetch_iot_credentials_async,
    fetch_iot_credentials_sync,
)


def test_sync_fetch_returns_dataclass(fake_facade) -> None:
    creds = fetch_iot_credentials_sync(fake_facade)
    assert isinstance(creds, IotCredentials)
    assert creds.endpoint == "abc-ats.iot.us-east-1.amazonaws.com"
    assert creds.presigned_wss_url.startswith("wss://")
    assert creds.topic_prefix == "axonpush/org_1"
    assert creds.env_slug == "default"
    assert creds.client_id == "k-test-abc"
    assert creds.region == "us-east-1"


def test_sync_fetch_invokes_generated_op(fake_facade) -> None:
    fetch_iot_credentials_sync(fake_facade)
    assert fake_facade.invoke_calls
    op, _kwargs = fake_facade.invoke_calls[0]
    assert op is _gen


def test_sync_fetch_parses_expires_at_with_z_suffix(fake_facade) -> None:
    fake_facade._dto.expires_at = "2099-01-01T00:00:00Z"
    creds = fetch_iot_credentials_sync(fake_facade)
    assert creds.expires_at.year == 2099
    assert creds.expires_at.tzinfo is not None


def test_sync_fetch_raises_when_invoke_returns_none() -> None:
    class _NoneFacade:
        def _invoke(self, op, **kwargs):
            return None

    with pytest.raises(ConnectionError, match="iot-credentials"):
        fetch_iot_credentials_sync(_NoneFacade())


def test_expires_in_returns_positive_seconds(fake_facade) -> None:
    creds = fetch_iot_credentials_sync(fake_facade)
    assert creds.expires_in() > 3500


@pytest.mark.asyncio
async def test_async_fetch_returns_dataclass(fake_async_facade) -> None:
    creds = await fetch_iot_credentials_async(fake_async_facade)
    assert isinstance(creds, IotCredentials)
    assert creds.topic_prefix == "axonpush/org_1"


@pytest.mark.asyncio
async def test_async_fetch_raises_when_invoke_returns_none() -> None:
    class _NoneFacade:
        async def _invoke(self, op, **kwargs):
            return None

    with pytest.raises(ConnectionError, match="iot-credentials"):
        await fetch_iot_credentials_async(_NoneFacade())
