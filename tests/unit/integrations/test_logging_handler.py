"""Unit tests for :class:`AxonPushLoggingHandler`.

Uses the duck-typed :class:`FakeSyncClient` so the tests don't depend on
Stream A's transport or Stream B's resources — just on the
``client.events.publish`` contract.
"""

from __future__ import annotations

import logging
from typing import Iterator

import pytest

from axonpush.integrations.logging_handler import (
    DEFAULT_EXCLUDED_LOGGERS,
    AxonPushLoggingHandler,
)
from axonpush.integrations.logging_handler import _SelfRecursionFilter

from .conftest import FakeSyncClient


@pytest.fixture()
def isolated_logger() -> Iterator[logging.Logger]:
    name = f"axonpush.test.{id(object())}"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger
    for h in list(logger.handlers):
        logger.removeHandler(h)


class TestPayload:
    def test_emits_app_log_event(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        handler = AxonPushLoggingHandler(
            client=fake_sync_client,
            channel_id="ch_test",
            service_name="myapp",
            mode="sync",
        )
        isolated_logger.addHandler(handler)
        isolated_logger.error("connection refused")

        assert len(fake_sync_client.events.calls) == 1
        call = fake_sync_client.events.calls[0]
        assert call["channel_id"] == "ch_test"
        assert call["event_type"].value == "app.log"
        assert call["payload"]["severityText"] == "ERROR"
        assert call["payload"]["severityNumber"] == 17
        assert call["payload"]["body"] == "connection refused"
        assert call["payload"]["resource"]["service.name"] == "myapp"
        assert call["metadata"]["framework"] == "stdlib-logging"

    def test_severity_mapping(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        isolated_logger.addHandler(
            AxonPushLoggingHandler(client=fake_sync_client, channel_id="ch_x", mode="sync")
        )
        cases = [
            (isolated_logger.debug, "d", 5, "DEBUG"),
            (isolated_logger.info, "i", 9, "INFO"),
            (isolated_logger.warning, "w", 13, "WARN"),
            (isolated_logger.error, "e", 17, "ERROR"),
            (isolated_logger.critical, "c", 21, "FATAL"),
        ]
        for log_fn, msg, expected_num, expected_text in cases:
            log_fn(msg)
        assert len(fake_sync_client.events.calls) == 5
        for call, (_, _, num, text) in zip(fake_sync_client.events.calls, cases):
            assert call["payload"]["severityNumber"] == num
            assert call["payload"]["severityText"] == text

    def test_extra_kwargs_become_attributes(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        isolated_logger.addHandler(
            AxonPushLoggingHandler(client=fake_sync_client, channel_id="ch_x", mode="sync")
        )
        isolated_logger.error("auth fail", extra={"user_id": 42, "ip": "1.2.3.4"})
        attrs = fake_sync_client.events.calls[0]["payload"]["attributes"]
        assert attrs["user_id"] == 42
        assert attrs["ip"] == "1.2.3.4"
        assert "code.filepath" in attrs
        assert attrs["logger.name"] == isolated_logger.name

    def test_agent_log_event_type(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        isolated_logger.addHandler(
            AxonPushLoggingHandler(
                client=fake_sync_client,
                channel_id="ch_x",
                source="agent",
                mode="sync",
            )
        )
        isolated_logger.info("agent thinking")
        assert fake_sync_client.events.calls[0]["event_type"].value == "agent.log"

    def test_invalid_source_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="source must be"):
            AxonPushLoggingHandler(
                client=fake_sync_client,
                channel_id="ch_x",
                source="bogus",
                mode="sync",
            )

    def test_invalid_mode_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="mode must be"):
            AxonPushLoggingHandler(
                client=fake_sync_client,
                channel_id="ch_x",
                mode="bogus",  # type: ignore[arg-type]
            )

    def test_resource_omitted_when_no_service_info(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        isolated_logger.addHandler(
            AxonPushLoggingHandler(client=fake_sync_client, channel_id="ch_x", mode="sync")
        )
        isolated_logger.info("plain")
        assert "resource" not in fake_sync_client.events.calls[0]["payload"]

    def test_emit_swallows_publish_exception(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        handler = AxonPushLoggingHandler(client=fake_sync_client, channel_id="ch_x", mode="sync")
        handler.handleError = lambda record: None  # type: ignore[method-assign]
        isolated_logger.addHandler(handler)
        # must not raise
        isolated_logger.error("boom")


class TestChannelIdCoercion:
    def test_int_channel_id_emits_deprecation(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning, match="channel_id as int"):
            handler = AxonPushLoggingHandler(client=fake_sync_client, channel_id=42, mode="sync")
        # And the publish still goes out with the stringified id.
        log = logging.getLogger("axonpush.test.coerce")
        log.propagate = False
        log.addHandler(handler)
        log.error("x")
        assert fake_sync_client.events.calls[0]["channel_id"] == "42"


class TestExclusionAndReentrancy:
    def test_default_exclusions(self) -> None:
        assert "axonpush" in DEFAULT_EXCLUDED_LOGGERS
        assert any(p.startswith("httpx") for p in DEFAULT_EXCLUDED_LOGGERS)
        assert any(p.startswith("httpcore") for p in DEFAULT_EXCLUDED_LOGGERS)

    def _make_record(self, name: str) -> logging.LogRecord:
        return logging.LogRecord(
            name=name,
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="x",
            args=None,
            exc_info=None,
        )

    def test_exact_match_excluded(self) -> None:
        f = _SelfRecursionFilter(exact=frozenset({"axonpush"}), prefixes=("httpx",))
        assert f.filter(self._make_record("axonpush")) is False
        assert f.filter(self._make_record("axonpush.user.foo")) is True

    def test_prefix_match_excluded(self) -> None:
        f = _SelfRecursionFilter(exact=frozenset(), prefixes=("httpx", "httpcore"))
        assert f.filter(self._make_record("httpx._client")) is False
        assert f.filter(self._make_record("httpcore.connection")) is False
        assert f.filter(self._make_record("myapp.module")) is True

    def test_user_extra_prefixes(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        handler = AxonPushLoggingHandler(
            client=fake_sync_client,
            channel_id="ch_x",
            mode="sync",
            exclude_loggers=["noisy"],
        )
        # The user-supplied prefix is additive on top of defaults.
        record = self._make_record("noisy.thing")
        assert handler.filters[0].filter(record) is False

    def test_reentrancy_guard_drops_publisher_records(
        self, fake_sync_client: FakeSyncClient, isolated_logger: logging.Logger
    ) -> None:
        from axonpush.integrations import _publisher as pub_mod

        handler = AxonPushLoggingHandler(client=fake_sync_client, channel_id="ch_x", mode="sync")
        isolated_logger.addHandler(handler)
        token = pub_mod._in_publisher_path.set(True)
        try:
            isolated_logger.error("inside publisher path")
        finally:
            pub_mod._in_publisher_path.reset(token)
        assert fake_sync_client.events.calls == []


class TestDictConfigConstructor:
    def test_builds_client_from_credential_kwargs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict = {}

        class FakeAxon:
            def __init__(self, **kwargs: object) -> None:
                captured.update(kwargs)
                self.events = type("E", (), {"publish": lambda **_: None})()

        monkeypatch.setattr("axonpush.client.AxonPush", FakeAxon)
        AxonPushLoggingHandler(
            channel_id="ch_x",
            api_key="ak_test",
            tenant_id="t_1",
            base_url="http://localhost:3000",
            mode="sync",
        )
        assert captured == {
            "api_key": "ak_test",
            "tenant_id": "t_1",
            "base_url": "http://localhost:3000",
        }

    def test_credentials_and_client_are_mutually_exclusive(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        with pytest.raises(ValueError, match="not both"):
            AxonPushLoggingHandler(
                client=fake_sync_client,
                channel_id="ch_x",
                api_key="ak_test",
                mode="sync",
            )

    def test_missing_credentials_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for v in ("AXONPUSH_API_KEY", "AXONPUSH_TENANT_ID", "AXONPUSH_BASE_URL"):
            monkeypatch.delenv(v, raising=False)
        with pytest.raises(ValueError, match="provide either client="):
            AxonPushLoggingHandler(channel_id="ch_x", mode="sync")
