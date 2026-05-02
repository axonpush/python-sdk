"""Unit tests for ``Apps`` / ``AsyncApps`` resources."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import pytest

from axonpush._internal.api.api.apps import (
    apps_controller_create_app as _create_op,
    apps_controller_delete_app as _delete_op,
    apps_controller_edit_app as _edit_op,
    apps_controller_get_all_apps as _list_op,
    apps_controller_get_app as _get_op,
)
from axonpush._internal.api.models import CreateAppDto
from axonpush.resources.apps import Apps, AsyncApps

APP_ID = "app-uuid-aaaa"


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


class TestSyncApps:
    def test_list_dispatches_list_op(self) -> None:
        fake = FakeSyncClient()
        Apps(fake).list()
        op, kwargs = fake.calls[0]
        assert op is _list_op
        assert kwargs == {}

    def test_get_dispatches_get_op(self) -> None:
        fake = FakeSyncClient()
        Apps(fake).get(APP_ID)
        op, kwargs = fake.calls[0]
        assert op is _get_op
        assert kwargs == {"id": APP_ID}

    def test_create_builds_dto(self) -> None:
        fake = FakeSyncClient()
        Apps(fake).create("checkout-prod")
        op, kwargs = fake.calls[0]
        assert op is _create_op
        body = kwargs["body"]
        assert isinstance(body, CreateAppDto)
        assert body.name == "checkout-prod"

    def test_update_passes_id_and_body(self) -> None:
        fake = FakeSyncClient()
        Apps(fake).update(APP_ID, name="renamed")
        op, kwargs = fake.calls[0]
        assert op is _edit_op
        assert kwargs["id"] == APP_ID
        assert isinstance(kwargs["body"], CreateAppDto)
        assert kwargs["body"].name == "renamed"

    def test_delete_dispatches_delete_op(self) -> None:
        fake = FakeSyncClient()
        Apps(fake).delete(APP_ID)
        op, kwargs = fake.calls[0]
        assert op is _delete_op
        assert kwargs == {"id": APP_ID}


class TestAsyncApps:
    @pytest.mark.asyncio
    async def test_list_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient()
        await AsyncApps(fake).list()
        op, kwargs = fake.calls[0]
        assert op is _list_op
        assert kwargs == {}

    @pytest.mark.asyncio
    async def test_create_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient()
        await AsyncApps(fake).create("svc-a")
        op, kwargs = fake.calls[0]
        assert op is _create_op
        assert isinstance(kwargs["body"], CreateAppDto)
