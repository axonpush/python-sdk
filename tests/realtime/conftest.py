"""Realtime test fixtures — fake facade so tests don't need a live transport."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from axonpush._internal.api.models.iot_credentials_response_dto import (
    IotCredentialsResponseDto,
)


def _credentials_dto(*, expires_in_seconds: int = 3600) -> IotCredentialsResponseDto:
    return IotCredentialsResponseDto(
        endpoint="abc-ats.iot.us-east-1.amazonaws.com",
        presigned_wss_url=("wss://abc-ats.iot.us-east-1.amazonaws.com/mqtt?X-Amz=token"),
        expires_at=(datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).isoformat(),
        topic_prefix="axonpush/org_1",
        env_slug="default",
        topic_template="axonpush/org_1/{envSlug}/{appId}/{channelId}/{eventType}/{agentId}",
        client_id="k-test-abc",
        region="us-east-1",
    )


class _FakeFacade:
    """Sync stand-in for :class:`AxonPush` — only the bits realtime touches."""

    def __init__(self, *, dto: IotCredentialsResponseDto | None = None) -> None:
        self._dto = dto if dto is not None else _credentials_dto()
        self.invoke_calls: list[Any] = []

    def _invoke(self, op: Any, **kwargs: Any) -> Any:
        self.invoke_calls.append((op, kwargs))
        return self._dto


class _AsyncFakeFacade:
    """Async stand-in for :class:`AsyncAxonPush`."""

    def __init__(self, *, dto: IotCredentialsResponseDto | None = None) -> None:
        self._dto = dto if dto is not None else _credentials_dto()
        self.invoke_calls: list[Any] = []

    async def _invoke(self, op: Any, **kwargs: Any) -> Any:
        self.invoke_calls.append((op, kwargs))
        return self._dto


@pytest.fixture()
def credentials_dto() -> IotCredentialsResponseDto:
    return _credentials_dto()


@pytest.fixture()
def fake_facade() -> _FakeFacade:
    return _FakeFacade()


@pytest.fixture()
def fake_async_facade() -> _AsyncFakeFacade:
    return _AsyncFakeFacade()
