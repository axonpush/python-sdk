"""Unit tests for ``Channels`` / ``AsyncChannels`` resources."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import pytest

from axonpush._internal.api.api.channels import (
    channel_controller_create_channel as _create_op,
    channel_controller_delete_channel as _delete_op,
    channel_controller_get_channel as _get_op,
    channel_controller_update_channel as _update_op,
)
from axonpush._internal.api.models import CreateChannelDto
from axonpush.resources.channels import AsyncChannels, Channels

APP_ID = "app-uuid-aaaa"
CHANNEL_ID = "ch-uuid-bbbb"


class FakeSyncClient:
    def __init__(self, return_value: Any = None) -> None:
        self.calls: list[tuple[Callable[..., Any], dict[str, Any]]] = []
        self.return_value = return_value

    def _invoke(self, op: Callable[..., Any], /, **kwargs: Any) -> Any:
        self.calls.append((op, kwargs))
        return self.return_value


class FakeAsyncClient:
    def __init__(self, return_value: Any = None) -> None:
        self.calls: list[tuple[Callable[..., Awaitable[Any]], dict[str, Any]]] = []
        self.return_value = return_value

    async def _invoke(self, op: Callable[..., Awaitable[Any]], /, **kwargs: Any) -> Any:
        self.calls.append((op, kwargs))
        return self.return_value


class TestSyncChannels:
    def test_get_dispatches_get_op(self) -> None:
        fake = FakeSyncClient()
        Channels(fake).get(CHANNEL_ID)
        op, kwargs = fake.calls[0]
        assert op is _get_op
        assert kwargs == {"id": CHANNEL_ID}

    def test_create_builds_dto(self) -> None:
        fake = FakeSyncClient()
        Channels(fake).create("alerts", APP_ID)
        op, kwargs = fake.calls[0]
        assert op is _create_op
        body = kwargs["body"]
        assert isinstance(body, CreateChannelDto)
        assert body.name == "alerts"
        assert body.app_id == APP_ID

    def test_update_dispatches_update_op(self) -> None:
        fake = FakeSyncClient()
        Channels(fake).update(CHANNEL_ID)
        op, kwargs = fake.calls[0]
        assert op is _update_op
        assert kwargs == {"id": CHANNEL_ID}

    def test_delete_dispatches_delete_op(self) -> None:
        fake = FakeSyncClient()
        Channels(fake).delete(CHANNEL_ID)
        op, kwargs = fake.calls[0]
        assert op is _delete_op
        assert kwargs == {"id": CHANNEL_ID}


class TestAsyncChannels:
    @pytest.mark.asyncio
    async def test_create_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient()
        await AsyncChannels(fake).create("alerts", APP_ID)
        op, kwargs = fake.calls[0]
        assert op is _create_op
        assert isinstance(kwargs["body"], CreateChannelDto)

    @pytest.mark.asyncio
    async def test_get_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient()
        await AsyncChannels(fake).get(CHANNEL_ID)
        op, kwargs = fake.calls[0]
        assert op is _get_op
        assert kwargs == {"id": CHANNEL_ID}
