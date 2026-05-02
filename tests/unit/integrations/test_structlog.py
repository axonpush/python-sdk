"""Unit tests for the structlog processor."""

from __future__ import annotations

from typing import Iterator

import pytest

pytest.importorskip("structlog")

import structlog  # noqa: E402

from axonpush.integrations.structlog import axonpush_structlog_processor  # noqa: E402

from .conftest import FakeSyncClient  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_structlog() -> Iterator[None]:
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


class TestStructlogProcessor:
    def test_emits_app_log_event(self, fake_sync_client: FakeSyncClient) -> None:
        proc = axonpush_structlog_processor(
            client=fake_sync_client,
            channel_id="ch_x",
            service_name="myapp",
            mode="sync",
        )
        proc(None, "error", {"event": "auth fail", "user_id": 42})
        assert len(fake_sync_client.events.calls) == 1
        call = fake_sync_client.events.calls[0]
        assert call["channel_id"] == "ch_x"
        assert call["event_type"].value == "app.log"
        assert call["payload"]["body"] == "auth fail"
        assert call["payload"]["severityText"] == "ERROR"
        assert call["payload"]["attributes"]["user_id"] == 42
        assert call["metadata"]["framework"] == "structlog"

    def test_returns_event_dict_unchanged(self, fake_sync_client: FakeSyncClient) -> None:
        proc = axonpush_structlog_processor(client=fake_sync_client, channel_id="ch_x", mode="sync")
        ed = {"event": "x", "foo": 1}
        result = proc(None, "info", ed)
        assert result is ed

    def test_agent_log_source(self, fake_sync_client: FakeSyncClient) -> None:
        proc = axonpush_structlog_processor(
            client=fake_sync_client,
            channel_id="ch_x",
            source="agent",
            mode="sync",
        )
        proc(None, "info", {"event": "thinking"})
        assert fake_sync_client.events.calls[0]["event_type"].value == "agent.log"

    def test_invalid_source_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="source must be"):
            axonpush_structlog_processor(
                client=fake_sync_client,
                channel_id="ch_x",
                source="bogus",
                mode="sync",
            )

    def test_invalid_mode_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="mode must be"):
            axonpush_structlog_processor(
                client=fake_sync_client,
                channel_id="ch_x",
                mode="bogus",  # type: ignore[arg-type]
            )

    def test_int_channel_id_emits_deprecation(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            proc = axonpush_structlog_processor(client=fake_sync_client, channel_id=42, mode="sync")
        proc(None, "info", {"event": "x"})
        assert fake_sync_client.events.calls[0]["channel_id"] == "42"

    def test_publish_exception_swallowed(self, fake_sync_client: FakeSyncClient) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        proc = axonpush_structlog_processor(client=fake_sync_client, channel_id="ch_x", mode="sync")
        proc(None, "error", {"event": "survives"})

    def test_reentrancy_guard_drops_records(self, fake_sync_client: FakeSyncClient) -> None:
        from axonpush.integrations import _publisher as p

        proc = axonpush_structlog_processor(client=fake_sync_client, channel_id="ch_x", mode="sync")
        token = p._in_publisher_path.set(True)
        try:
            proc(None, "info", {"event": "inside"})
        finally:
            p._in_publisher_path.reset(token)
        assert fake_sync_client.events.calls == []

    def test_iso_timestamp_parsing(self, fake_sync_client: FakeSyncClient) -> None:
        proc = axonpush_structlog_processor(client=fake_sync_client, channel_id="ch_x", mode="sync")
        proc(None, "info", {"event": "x", "timestamp": "2025-01-01T00:00:00Z"})
        nano = fake_sync_client.events.calls[0]["payload"]["timeUnixNano"]
        assert isinstance(nano, str)
        # Just check it's a numeric string with at least 19 digits (ns resolution)
        assert nano.isdigit() and len(nano) >= 18

    def test_numeric_timestamp_parsing(self, fake_sync_client: FakeSyncClient) -> None:
        proc = axonpush_structlog_processor(client=fake_sync_client, channel_id="ch_x", mode="sync")
        proc(None, "info", {"event": "x", "timestamp": 1704067200.0})
        nano = fake_sync_client.events.calls[0]["payload"]["timeUnixNano"]
        assert nano == "1704067200000000000"
