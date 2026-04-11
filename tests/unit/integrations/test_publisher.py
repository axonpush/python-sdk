"""Tests for the shared BackgroundPublisher helper.

Covers the queue/worker-thread path used by all four observability
integrations. The individual integration tests run with ``mode="sync"``
so their payload assertions stay deterministic; this file is the one
place that exercises the background path end-to-end.
"""
from __future__ import annotations

import logging
import os
import sys
import time

import httpx
import pytest

from axonpush import AxonPush
from axonpush.integrations._publisher import (
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    DROP_WARNING_INTERVAL_S,
    detect_serverless,
    flush_after_invocation,
)

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _ack() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "test",
            "payload": {},
            "eventType": "app.log",
        },
    )


def _publish_kwargs(identifier: str = "test") -> dict:
    return {
        "identifier": identifier,
        "payload": {"body": identifier},
        "channel_id": 5,
        "event_type": "app.log",
    }


class TestBackgroundPublisherBasics:
    def test_submit_drains_on_background_thread(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c)
            try:
                for i in range(5):
                    pub.submit(_publish_kwargs(f"record_{i}"))
                pub.flush(timeout=2.0)
            finally:
                pub.close()
        assert route.call_count == 5

    def test_flush_blocks_until_drained(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c)
            try:
                pub.submit(_publish_kwargs("a"))
                pub.submit(_publish_kwargs("b"))
                pub.flush(timeout=2.0)
                assert route.call_count == 2
            finally:
                pub.close()

    def test_flush_respects_timeout(self, mock_router):
        """flush(timeout=0) must return promptly even with pending work."""
        mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c, queue_size=100)
            try:
                for i in range(10):
                    pub.submit(_publish_kwargs(f"x_{i}"))
                start = time.monotonic()
                pub.flush(timeout=0.0)
                elapsed = time.monotonic() - start
                assert elapsed < 0.2
            finally:
                pub.close()

    def test_close_drains_pending_records(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c)
            for i in range(3):
                pub.submit(_publish_kwargs(f"r_{i}"))
            pub.close()
        assert route.call_count == 3

    def test_close_is_idempotent(self, mock_router):
        mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c)
            pub.close()
            pub.close()  # must not raise
            pub.close()

    def test_submit_after_close_is_silently_dropped(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            pub = BackgroundPublisher(c)
            pub.close()
            pub.submit(_publish_kwargs("after_close"))
        assert route.call_count == 0


class TestBackgroundPublisherOverflow:
    def test_full_queue_drops_records(self):
        """Saturate a publisher with a slow fake client and assert drops."""
        class SlowEvents:
            def publish(self, **kwargs):
                time.sleep(0.5)

        class SlowClient:
            def __init__(self):
                self.events = SlowEvents()

        pub = BackgroundPublisher(SlowClient(), queue_size=2)
        try:
            for i in range(20):
                pub.submit(_publish_kwargs(f"x_{i}"))
            assert pub._drop_counter >= 10
        finally:
            pub.close()

    def test_drop_warning_is_rate_limited(self, caplog):
        class SlowEvents:
            def publish(self, **kwargs):
                time.sleep(0.5)

        class SlowClient:
            def __init__(self):
                self.events = SlowEvents()

        caplog.set_level(logging.WARNING, logger="axonpush")
        pub = BackgroundPublisher(SlowClient(), queue_size=1)
        try:
            for i in range(30):
                pub.submit(_publish_kwargs(f"x_{i}"))
            warnings = [r for r in caplog.records if "queue full" in r.message]
            assert len(warnings) == 1, (
                f"expected exactly one rate-limited warning, got {len(warnings)}"
            )
        finally:
            pub.close()

    def test_worker_exception_does_not_kill_thread(self, mock_router):
        """A publish failure must not take down the worker thread."""
        route = mock_router.post("/event").mock(
            side_effect=[httpx.ConnectError("boom"), _ack(), _ack()]
        )
        with AxonPush(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            fail_open=False,
        ) as c:
            pub = BackgroundPublisher(c)
            try:
                pub.submit(_publish_kwargs("first_fails"))
                time.sleep(0.1)
                pub.submit(_publish_kwargs("second_ok"))
                pub.submit(_publish_kwargs("third_ok"))
                pub.flush(timeout=2.0)
            finally:
                pub.close()
        assert route.call_count == 3


class TestServerlessDetection:
    _VARS = ("AWS_LAMBDA_FUNCTION_NAME", "FUNCTION_TARGET", "AZURE_FUNCTIONS_ENVIRONMENT")

    def _clear_all(self, monkeypatch):
        for var in self._VARS:
            monkeypatch.delenv(var, raising=False)

    def test_returns_none_when_no_env(self, monkeypatch):
        self._clear_all(monkeypatch)
        assert detect_serverless() is None

    def test_detects_aws_lambda(self, monkeypatch):
        self._clear_all(monkeypatch)
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "my-function")
        assert detect_serverless() == "AWS Lambda"

    def test_detects_google_cloud_functions(self, monkeypatch):
        self._clear_all(monkeypatch)
        monkeypatch.setenv("FUNCTION_TARGET", "handler")
        assert detect_serverless() == "Google Cloud Functions"

    def test_detects_azure_functions(self, monkeypatch):
        self._clear_all(monkeypatch)
        monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
        assert detect_serverless() == "Azure Functions"


class TestFlushAfterInvocation:
    class _FakeHandler:
        def __init__(self):
            self.flushes = 0
            self.last_timeout = None

        def flush(self, timeout=None):
            self.flushes += 1
            self.last_timeout = timeout

    def test_wraps_and_flushes_on_success(self):
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn(x):
            return x * 2

        assert fn(3) == 6
        assert h.flushes == 1

    def test_flushes_even_when_handler_raises(self):
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            fn()
        assert h.flushes == 1

    def test_supports_multiple_handlers(self):
        h1 = self._FakeHandler()
        h2 = self._FakeHandler()

        @flush_after_invocation(h1, h2)
        def fn():
            return "ok"

        assert fn() == "ok"
        assert h1.flushes == 1
        assert h2.flushes == 1

    def test_default_timeout_is_5_seconds(self):
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn():
            pass

        fn()
        assert h.last_timeout == 5.0

    def test_custom_timeout_is_forwarded(self):
        h = self._FakeHandler()

        @flush_after_invocation(h, timeout=1.5)
        def fn():
            pass

        fn()
        assert h.last_timeout == 1.5

    def test_handler_flush_error_is_swallowed(self, caplog):
        class ExplodingHandler:
            def flush(self, timeout=None):
                raise RuntimeError("flush failed")

        @flush_after_invocation(ExplodingHandler())
        def fn():
            return "ok"

        caplog.set_level(logging.WARNING, logger="axonpush")
        assert fn() == "ok"
        assert any("flush() raised" in r.message for r in caplog.records)


class TestConstants:
    def test_defaults_are_sensible(self):
        assert DEFAULT_QUEUE_SIZE == 1000
        assert DEFAULT_SHUTDOWN_TIMEOUT_S == 2.0
        assert DROP_WARNING_INTERVAL_S == 10.0


@pytest.mark.skipif(sys.platform == "win32", reason="fork unsupported on Windows")
class TestForkSafety:
    def test_register_at_fork_hook_is_installed(self):
        """The module registers a child-fork handler at import time."""
        assert hasattr(os, "register_at_fork"), "Python too old for register_at_fork"
        # Can't easily introspect the registered callback — this test is a
        # belt-and-braces check that the import didn't raise on register_at_fork.
        from axonpush.integrations import _publisher
        assert _publisher._reset_all_publishers_after_fork is not None
