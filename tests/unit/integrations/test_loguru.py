"""Unit tests for the Loguru sink."""
from __future__ import annotations

from typing import Iterator

import pytest

pytest.importorskip("loguru")

from loguru import logger as loguru_logger  # noqa: E402

from axonpush.integrations.loguru import create_axonpush_loguru_sink  # noqa: E402

from .conftest import FakeSyncClient  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_loguru() -> Iterator[None]:
    loguru_logger.remove()
    yield
    loguru_logger.remove()


class TestLoguruSink:
    def test_emits_app_log_event(self, fake_sync_client: FakeSyncClient) -> None:
        sink = create_axonpush_loguru_sink(
            client=fake_sync_client,
            channel_id="ch_x",
            service_name="myapp",
            mode="sync",
        )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.error("connection refused")
        assert len(fake_sync_client.events.calls) == 1
        call = fake_sync_client.events.calls[0]
        assert call["channel_id"] == "ch_x"
        assert call["event_type"].value == "app.log"
        assert call["payload"]["body"] == "connection refused"
        assert call["payload"]["severityText"] == "ERROR"
        assert call["metadata"]["framework"] == "loguru"

    def test_extra_kwargs_become_attributes(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        sink = create_axonpush_loguru_sink(
            client=fake_sync_client, channel_id="ch_x", mode="sync"
        )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.bind(user_id=42).info("hi")
        attrs = fake_sync_client.events.calls[0]["payload"]["attributes"]
        assert attrs.get("user_id") == 42

    def test_agent_log_source(self, fake_sync_client: FakeSyncClient) -> None:
        sink = create_axonpush_loguru_sink(
            client=fake_sync_client,
            channel_id="ch_x",
            source="agent",
            mode="sync",
        )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.info("a")
        assert (
            fake_sync_client.events.calls[0]["event_type"].value == "agent.log"
        )

    def test_invalid_source_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="source must be"):
            create_axonpush_loguru_sink(
                client=fake_sync_client,
                channel_id="ch_x",
                source="bogus",
                mode="sync",
            )

    def test_invalid_mode_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="mode must be"):
            create_axonpush_loguru_sink(
                client=fake_sync_client,
                channel_id="ch_x",
                mode="bogus",  # type: ignore[arg-type]
            )

    def test_int_channel_id_emits_deprecation(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        with pytest.warns(DeprecationWarning):
            sink = create_axonpush_loguru_sink(
                client=fake_sync_client, channel_id=42, mode="sync"
            )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.info("x")
        assert fake_sync_client.events.calls[0]["channel_id"] == "42"

    def test_publish_exception_swallowed(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        sink = create_axonpush_loguru_sink(
            client=fake_sync_client, channel_id="ch_x", mode="sync"
        )
        loguru_logger.add(sink, serialize=True)
        loguru_logger.error("survives")

    def test_reentrancy_guard_drops_records(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        from axonpush.integrations import _publisher as p

        sink = create_axonpush_loguru_sink(
            client=fake_sync_client, channel_id="ch_x", mode="sync"
        )
        loguru_logger.add(sink, serialize=True)
        token = p._in_publisher_path.set(True)
        try:
            loguru_logger.info("inside")
        finally:
            p._in_publisher_path.reset(token)
        assert fake_sync_client.events.calls == []
