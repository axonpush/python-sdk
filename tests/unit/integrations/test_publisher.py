"""Tests for the publisher infrastructure (sync, async, RQ, helpers)."""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any, Dict

import pytest

from axonpush.integrations._publisher import (
    AsyncBackgroundPublisher,
    BackgroundPublisher,
    DEFAULT_QUEUE_SIZE,
    DEFAULT_SHUTDOWN_TIMEOUT_S,
    DROP_WARNING_INTERVAL_S,
    OverflowPolicy,
    detect_serverless,
    flush_after_invocation,
    in_publisher_path,
)

from .conftest import FakeAsyncClient, FakeSyncClient


def _publish_kwargs(identifier: str = "test") -> Dict[str, Any]:
    return {
        "identifier": identifier,
        "payload": {"body": identifier},
        "channel_id": "ch_test",
        "event_type": "app.log",
    }


class _SlowSyncEvents:
    def __init__(self, delay: float = 0.5) -> None:
        self.delay = delay
        self.count = 0

    def publish(self, **kwargs: Any) -> None:
        time.sleep(self.delay)
        self.count += 1


class _SlowSyncClient:
    def __init__(self, delay: float = 0.5) -> None:
        self.events = _SlowSyncEvents(delay)


class TestBackgroundPublisherBasics:
    def test_submit_drains_on_background_thread(self) -> None:
        client = FakeSyncClient()
        pub = BackgroundPublisher(client)
        try:
            for i in range(5):
                pub.submit(_publish_kwargs(f"r_{i}"))
            pub.flush(timeout=2.0)
        finally:
            pub.close()
        assert len(client.events.calls) == 5

    def test_flush_blocks_until_drained(self) -> None:
        client = FakeSyncClient()
        pub = BackgroundPublisher(client)
        try:
            pub.submit(_publish_kwargs("a"))
            pub.submit(_publish_kwargs("b"))
            pub.flush(timeout=2.0)
            assert len(client.events.calls) == 2
        finally:
            pub.close()

    def test_flush_respects_timeout(self) -> None:
        slow = _SlowSyncClient(delay=0.5)
        pub = BackgroundPublisher(slow, queue_size=100)
        try:
            for i in range(10):
                pub.submit(_publish_kwargs(f"x_{i}"))
            start = time.monotonic()
            pub.flush(timeout=0.0)
            elapsed = time.monotonic() - start
            assert elapsed < 0.2
        finally:
            pub.close(timeout=0.1)

    def test_close_drains_pending_records(self) -> None:
        client = FakeSyncClient()
        pub = BackgroundPublisher(client)
        for i in range(3):
            pub.submit(_publish_kwargs(f"r_{i}"))
        pub.close()
        assert len(client.events.calls) == 3

    def test_close_is_idempotent(self) -> None:
        client = FakeSyncClient()
        pub = BackgroundPublisher(client)
        pub.close()
        pub.close()
        pub.close()

    def test_submit_after_close_is_silently_dropped(self) -> None:
        client = FakeSyncClient()
        pub = BackgroundPublisher(client)
        pub.close()
        pub.submit(_publish_kwargs("after_close"))
        assert client.events.calls == []


class TestBackgroundPublisherOverflow:
    def test_drop_oldest_keeps_newest(self) -> None:
        slow = _SlowSyncClient(delay=0.5)
        pub = BackgroundPublisher(
            slow,
            queue_size=2,
            overflow_policy=OverflowPolicy.DROP_OLDEST,
        )
        try:
            for i in range(10):
                pub.submit(_publish_kwargs(f"r_{i}"))
            assert pub.dropped >= 5
        finally:
            pub.close(timeout=0.1)

    def test_drop_newest_keeps_oldest(self) -> None:
        slow = _SlowSyncClient(delay=0.5)
        pub = BackgroundPublisher(
            slow,
            queue_size=2,
            overflow_policy=OverflowPolicy.DROP_NEWEST,
        )
        try:
            for i in range(10):
                pub.submit(_publish_kwargs(f"r_{i}"))
            assert pub.dropped >= 5
        finally:
            pub.close(timeout=0.1)

    def test_drop_warning_is_rate_limited(self, caplog: pytest.LogCaptureFixture) -> None:
        slow = _SlowSyncClient(delay=0.5)
        caplog.set_level(logging.WARNING)
        pub = BackgroundPublisher(slow, queue_size=1)
        try:
            for i in range(30):
                pub.submit(_publish_kwargs(f"x_{i}"))
            warnings = [r for r in caplog.records if "queue full" in r.message]
            assert len(warnings) == 1
        finally:
            pub.close(timeout=0.1)

    def test_worker_survives_publish_exception(self) -> None:
        from unittest.mock import patch

        from axonpush.integrations import _publisher as p

        client = FakeSyncClient()
        client.events.exception = RuntimeError("boom")
        # Isolate the rate-limit cache and spy on the logger together —
        # otherwise a sibling test's daemon thread can seed
        # `_publish_failure_last_warn` with the same `(None, None)` key and
        # the rate-limiter swallows the warning we want to assert.
        with (
            patch.object(p, "_internal_logger") as spy_logger,
            patch.dict(p._publish_failure_last_warn, clear=True),
        ):
            pub = BackgroundPublisher(client)
            try:
                pub.submit(_publish_kwargs("first_fails"))
                pub.flush(timeout=1.0)
                client.events.exception = None
                pub.submit(_publish_kwargs("second_ok"))
                pub.flush(timeout=1.0)
            finally:
                pub.close()
            assert len(client.events.calls) == 2
            assert spy_logger.warning.call_count + spy_logger.error.call_count >= 1


class TestPublisherReentrancyGuard:
    def test_in_publisher_path_set_during_publish(self) -> None:
        seen: list[bool] = []

        class Probe:
            def publish(self, **_: Any) -> None:
                seen.append(in_publisher_path())

        class ProbeClient:
            def __init__(self) -> None:
                self.events = Probe()

        pub = BackgroundPublisher(ProbeClient())
        try:
            pub.submit(_publish_kwargs())
            pub.flush(timeout=1.0)
        finally:
            pub.close()
        assert seen == [True]

    def test_in_publisher_path_cleared_outside(self) -> None:
        assert in_publisher_path() is False


class TestAsyncBackgroundPublisher:
    async def test_submit_drains(self) -> None:
        client = FakeAsyncClient()
        pub = AsyncBackgroundPublisher(client)
        try:
            for i in range(5):
                pub.submit(_publish_kwargs(f"r_{i}"))
            await pub.flush(timeout=2.0)
        finally:
            await pub.aclose()
        assert len(client.events.calls) == 5

    async def test_aclose_drains_pending(self) -> None:
        client = FakeAsyncClient()
        pub = AsyncBackgroundPublisher(client)
        for i in range(3):
            pub.submit(_publish_kwargs(f"r_{i}"))
        await pub.aclose(timeout=2.0)
        assert len(client.events.calls) == 3

    async def test_aclose_is_idempotent(self) -> None:
        client = FakeAsyncClient()
        pub = AsyncBackgroundPublisher(client)
        await pub.aclose()
        await pub.aclose()

    async def test_submit_after_close_is_dropped(self) -> None:
        client = FakeAsyncClient()
        pub = AsyncBackgroundPublisher(client)
        await pub.aclose()
        pub.submit(_publish_kwargs("after_close"))
        assert client.events.calls == []

    async def test_publish_exception_does_not_kill_worker(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        client = FakeAsyncClient()
        client.events.exception = RuntimeError("nope")
        caplog.set_level(logging.WARNING)
        pub = AsyncBackgroundPublisher(client)
        try:
            pub.submit(_publish_kwargs("fails"))
            await pub.flush(timeout=1.0)
            client.events.exception = None
            pub.submit(_publish_kwargs("ok"))
            await pub.flush(timeout=1.0)
        finally:
            await pub.aclose()
        assert len(client.events.calls) == 2

    async def test_reentrancy_guard_set_during_async_publish(self) -> None:
        seen: list[bool] = []

        class Probe:
            async def publish(self, **_: Any) -> None:
                seen.append(in_publisher_path())

        class ProbeClient:
            def __init__(self) -> None:
                self.events = Probe()

        pub = AsyncBackgroundPublisher(ProbeClient())
        try:
            pub.submit(_publish_kwargs())
            await pub.flush(timeout=1.0)
        finally:
            await pub.aclose()
        assert seen == [True]


class TestAsyncPublisherWithoutLoop:
    def test_submit_silently_drops_when_no_loop(self) -> None:
        client = FakeAsyncClient()
        pub = AsyncBackgroundPublisher(client)
        # No running loop here — submit should no-op rather than crash.
        pub.submit(_publish_kwargs("nope"))
        assert client.events.calls == []


class TestServerlessDetection:
    _VARS = ("AWS_LAMBDA_FUNCTION_NAME", "FUNCTION_TARGET", "AZURE_FUNCTIONS_ENVIRONMENT")

    def _clear(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for v in self._VARS:
            monkeypatch.delenv(v, raising=False)

    def test_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear(monkeypatch)
        assert detect_serverless() is None

    def test_aws_lambda(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear(monkeypatch)
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "fn")
        assert detect_serverless() == "AWS Lambda"

    def test_gcf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear(monkeypatch)
        monkeypatch.setenv("FUNCTION_TARGET", "fn")
        assert detect_serverless() == "Google Cloud Functions"

    def test_azure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._clear(monkeypatch)
        monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
        assert detect_serverless() == "Azure Functions"


class TestFlushAfterInvocation:
    class _FakeHandler:
        def __init__(self) -> None:
            self.flushes = 0
            self.last_timeout: float | None = None

        def flush(self, timeout: float | None = None) -> None:
            self.flushes += 1
            self.last_timeout = timeout

    def test_wraps_and_flushes(self) -> None:
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn(x: int) -> int:
            return x * 2

        assert fn(3) == 6
        assert h.flushes == 1

    def test_flushes_on_exception(self) -> None:
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn() -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            fn()
        assert h.flushes == 1

    def test_default_timeout(self) -> None:
        h = self._FakeHandler()

        @flush_after_invocation(h)
        def fn() -> None:
            return None

        fn()
        assert h.last_timeout == 5.0

    def test_custom_timeout(self) -> None:
        h = self._FakeHandler()

        @flush_after_invocation(h, timeout=1.5)
        def fn() -> None:
            return None

        fn()
        assert h.last_timeout == 1.5

    def test_handler_flush_error_is_swallowed(self, caplog: pytest.LogCaptureFixture) -> None:
        class Exploding:
            def flush(self, timeout: float | None = None) -> None:
                raise RuntimeError("flush failed")

        @flush_after_invocation(Exploding())
        def fn() -> str:
            return "ok"

        caplog.set_level(logging.WARNING)
        assert fn() == "ok"
        assert any("flush() raised" in r.message for r in caplog.records)


class TestConstants:
    def test_defaults(self) -> None:
        assert DEFAULT_QUEUE_SIZE == 1000
        assert DEFAULT_SHUTDOWN_TIMEOUT_S == 2.0
        assert DROP_WARNING_INTERVAL_S == 10.0


@pytest.mark.skipif(sys.platform == "win32", reason="fork unsupported on Windows")
class TestForkSafety:
    def test_register_at_fork_hook_is_installed(self) -> None:
        assert hasattr(os, "register_at_fork")
        from axonpush.integrations import _publisher as p

        assert p._reset_all_publishers_after_fork is not None


class TestPublishFailureLogging:
    """The publisher's background loop uses ``_log_publish_failure`` to
    distinguish config errors (ValidationError, 4xx) from transient errors
    (connection / 5xx). Config errors get ERROR level with the operator
    hint surfaced — those don't fix themselves and the user needs to
    notice. Transient errors stay at WARNING.

    Each test stacks two patches:

    * ``patch.object(_publisher, "_internal_logger")`` — spy on the
      logger so we don't depend on caplog handler levels, propagation
      settings, or daemon-thread emit timing (all of which were sources
      of the original cross-Python-version flakiness).
    * ``patch.dict(_publisher._publish_failure_last_warn, clear=True)`` —
      give each test an isolated rate-limit cache. ``patch.dict``
      restores the original entries (and removes any new ones) on exit,
      so test order doesn't matter and a daemon thread from a sibling
      test cannot pollute the cache mid-test.
    """

    @staticmethod
    def _isolate() -> Any:
        from contextlib import ExitStack
        from unittest.mock import patch

        from axonpush.integrations import _publisher as p

        stack = ExitStack()
        spy = stack.enter_context(patch.object(p, "_internal_logger"))
        stack.enter_context(patch.dict(p._publish_failure_last_warn, clear=True))
        # Wrap the stack so callers can `with self._isolate() as spy:`.
        stack.spy_logger = spy  # type: ignore[attr-defined]
        return stack

    def test_validation_error_logs_at_error_with_hint(self) -> None:
        from axonpush.exceptions import ValidationError
        from axonpush.integrations._publisher import _log_publish_failure

        exc = ValidationError(
            "environment 'development' is not registered",
            status_code=400,
            code="invalid_environment",
            hint="set AXONPUSH_ENVIRONMENT to one of the configured slugs",
        )

        with self._isolate() as stack:
            _log_publish_failure(exc)
            spy_logger = stack.spy_logger

            spy_logger.error.assert_called_once()
            spy_logger.warning.assert_not_called()
            fmt, *args = spy_logger.error.call_args.args
            rendered = fmt % tuple(args)
            assert "configuration error" in rendered
            assert "set AXONPUSH_ENVIRONMENT" in rendered
            assert "invalid_environment" in rendered

    def test_4xx_other_than_429_treated_as_config_error(self) -> None:
        from axonpush.exceptions import AxonPushError
        from axonpush.integrations._publisher import _log_publish_failure

        with self._isolate() as stack:
            _log_publish_failure(
                AxonPushError("forbidden", status_code=403, code="forbidden")
            )
            spy_logger = stack.spy_logger

            spy_logger.error.assert_called_once()
            spy_logger.warning.assert_not_called()

    def test_connection_error_stays_at_warning(self) -> None:
        from axonpush.exceptions import APIConnectionError
        from axonpush.integrations._publisher import _log_publish_failure

        with self._isolate() as stack:
            _log_publish_failure(APIConnectionError("dns fail"))
            spy_logger = stack.spy_logger

            spy_logger.warning.assert_called_once()
            spy_logger.error.assert_not_called()

    def test_rate_limited_per_error_key(self) -> None:
        from axonpush.exceptions import ValidationError
        from axonpush.integrations._publisher import _log_publish_failure

        exc = ValidationError(
            "bad env", status_code=400, code="invalid_environment"
        )

        with self._isolate() as stack:
            _log_publish_failure(exc)
            _log_publish_failure(exc)
            _log_publish_failure(exc)
            assert stack.spy_logger.error.call_count == 1
