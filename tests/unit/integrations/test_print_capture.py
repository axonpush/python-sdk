"""Unit tests for ``setup_print_capture``."""

from __future__ import annotations

import sys
from typing import Iterator

import pytest

from axonpush.integrations.print_capture import (
    setup_print_capture,
)

from .conftest import FakeSyncClient


@pytest.fixture(autouse=True)
def _restore_streams() -> Iterator[None]:
    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    yield
    sys.stdout, sys.stderr = orig_stdout, orig_stderr


def _last_call(client: FakeSyncClient) -> dict:
    return client.events.calls[-1]


class TestPrintCapture:
    def test_print_emits_one_event_per_line(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            print("hello")
        finally:
            handle.unpatch()
        assert len(fake_sync_client.events.calls) == 1
        assert _last_call(fake_sync_client)["payload"]["body"] == "hello"

    def test_stderr_severity_error(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            print("oops", file=sys.stderr)
        finally:
            handle.unpatch()
        call = _last_call(fake_sync_client)
        assert call["payload"]["severityText"] == "ERROR"
        assert call["payload"]["severityNumber"] == 17

    def test_partial_line_buffered_until_newline(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            sys.stdout.write("partial")
            assert fake_sync_client.events.calls == []
            sys.stdout.write(" line\n")
        finally:
            handle.unpatch()
        assert _last_call(fake_sync_client)["payload"]["body"] == "partial line"

    def test_blank_lines_skipped(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            print("")
            print("\t  ")
            print("real")
        finally:
            handle.unpatch()
        assert len(fake_sync_client.events.calls) == 1
        assert _last_call(fake_sync_client)["payload"]["body"] == "real"

    def test_unpatch_restores_streams(self, fake_sync_client: FakeSyncClient) -> None:
        orig_out, orig_err = sys.stdout, sys.stderr
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        assert sys.stdout is not orig_out
        assert sys.stderr is not orig_err
        handle.unpatch()
        assert sys.stdout is orig_out
        assert sys.stderr is orig_err

    def test_unpatch_is_idempotent(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        handle.unpatch()
        handle.unpatch()

    def test_context_manager(self, fake_sync_client: FakeSyncClient) -> None:
        orig_out = sys.stdout
        with setup_print_capture(fake_sync_client, "ch_x", mode="sync"):
            print("inside")
        assert sys.stdout is orig_out
        assert _last_call(fake_sync_client)["payload"]["body"] == "inside"

    def test_event_type_app_when_source_app(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", source="app", mode="sync")
        try:
            print("x")
        finally:
            handle.unpatch()
        assert _last_call(fake_sync_client)["event_type"].value == "app.log"

    def test_event_type_agent_by_default(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            print("x")
        finally:
            handle.unpatch()
        assert _last_call(fake_sync_client)["event_type"].value == "agent.log"

    def test_invalid_source_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="source must be"):
            setup_print_capture(fake_sync_client, "ch_x", source="bogus", mode="sync")

    def test_publish_failure_does_not_crash_print(self, fake_sync_client: FakeSyncClient) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            print("survives")
        finally:
            handle.unpatch()

    def test_flush_emits_buffered_partial_line(self, fake_sync_client: FakeSyncClient) -> None:
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            sys.stdout.write("no newline")
            assert fake_sync_client.events.calls == []
            sys.stdout.flush()
        finally:
            handle.unpatch()
        assert _last_call(fake_sync_client)["payload"]["body"] == "no newline"


class TestChannelCoercion:
    def test_int_channel_id_warns(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            handle = setup_print_capture(fake_sync_client, 99, mode="sync")
        try:
            print("x")
        finally:
            handle.unpatch()
        assert fake_sync_client.events.calls[0]["channel_id"] == "99"


class TestAtexitHook:
    def test_handle_registered_in_live_set(self, fake_sync_client: FakeSyncClient) -> None:
        from axonpush.integrations import print_capture as pc

        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        try:
            assert handle in pc._LIVE_HANDLES
        finally:
            handle.unpatch()

    def test_unpatch_all_restores_streams(self, fake_sync_client: FakeSyncClient) -> None:
        from axonpush.integrations import print_capture as pc

        orig_out = sys.stdout
        handle = setup_print_capture(fake_sync_client, "ch_x", mode="sync")
        assert sys.stdout is not orig_out
        pc._unpatch_all_handles()
        assert sys.stdout is orig_out
        pc._unpatch_all_handles()
        handle.unpatch()
