"""Shared fixtures for integration unit tests.

Stream D's tests deliberately do NOT go through the real
:class:`axonpush.AxonPush` / :class:`AsyncAxonPush` clients — that would
couple the integration layer to Stream A's transport and Stream B's
resources, both of which are owned by other agents and may shift
underneath us between commits.

Instead we expose a duck-typed :class:`FakeSyncClient` /
:class:`FakeAsyncClient` whose ``events.publish`` method records every
call. The integrations rely only on ``client.events.publish(**kwargs)``
per the v0.0.10 contract, so the fakes are a complete substitute.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List

import pytest


class _FakeSyncEvents:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.exception: BaseException | None = None
        self._lock = threading.Lock()

    def publish(self, **kwargs: Any) -> Dict[str, Any]:
        with self._lock:
            self.calls.append(kwargs)
            if self.exception is not None:
                raise self.exception
        return {"id": len(self.calls), **kwargs}


class FakeSyncClient:
    """Duck-typed stand-in for :class:`axonpush.AxonPush`."""

    def __init__(self) -> None:
        self.events = _FakeSyncEvents()


class _FakeAsyncEvents:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.exception: BaseException | None = None

    async def publish(self, **kwargs: Any) -> Dict[str, Any]:
        self.calls.append(kwargs)
        if self.exception is not None:
            raise self.exception
        return {"id": len(self.calls), **kwargs}


class FakeAsyncClient:
    """Duck-typed stand-in for :class:`axonpush.AsyncAxonPush`."""

    def __init__(self) -> None:
        self.events = _FakeAsyncEvents()


@pytest.fixture()
def fake_sync_client() -> FakeSyncClient:
    return FakeSyncClient()


@pytest.fixture()
def fake_async_client() -> FakeAsyncClient:
    return FakeAsyncClient()


@pytest.fixture(autouse=True)
def _reset_publish_failure_cache() -> Any:
    """Isolate the publisher's rate-limit cache across tests.

    `_log_publish_failure` keeps a module-level dict keyed by
    ``(error_code, status_code)`` so a misconfigured deploy doesn't spam
    the log. Several integration tests inject a `RuntimeError` into a
    fake client to exercise the publisher's exception path; that path
    seeds ``(None, None)`` into the cache. Without isolation, any later
    test that asserts a record was emitted for a non-AxonPushError
    exception sees the rate-limit kick in instead and `caplog.records`
    stays empty — a flaky failure that surfaces on whichever Python
    version happens to schedule the polluting test first.
    """
    from axonpush.integrations import _publisher as p

    p._publish_failure_last_warn.clear()
    yield
    p._publish_failure_last_warn.clear()
