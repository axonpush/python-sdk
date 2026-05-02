"""Unit tests for the DeepAgents callback handlers."""

from __future__ import annotations

import uuid

import pytest

pytest.importorskip("deepagents")
pytest.importorskip("langchain_core")

from axonpush.integrations.deepagents import (  # noqa: E402
    AsyncAxonPushDeepAgentHandler,
    AxonPushDeepAgentHandler,
    _classify_tool_end,
    _classify_tool_start,
    get_deepagent_handler,
)

from .conftest import FakeAsyncClient, FakeSyncClient  # noqa: E402


class TestToolClassification:
    def test_planning_tool(self) -> None:
        assert _classify_tool_start("write_todos")[0] == "planning.update"
        assert _classify_tool_end("write_todos")[0] == "planning.complete"

    def test_subagent_tool(self) -> None:
        ident, et = _classify_tool_start("task")
        assert ident == "subagent.spawn"
        assert et.value == "agent.handoff"

    def test_filesystem_read(self) -> None:
        for name in ("read_file", "ls", "glob", "grep"):
            ident, _ = _classify_tool_start(name)
            assert ident == "filesystem.read"

    def test_sandbox_execute(self) -> None:
        assert _classify_tool_start("execute")[0] == "sandbox.execute"

    def test_unknown_falls_back(self) -> None:
        ident, et = _classify_tool_start("custom_thing")
        assert ident == "tool.custom_thing.start"
        assert et.value == "agent.tool_call.start"


class TestSyncHandler:
    def test_chain_start_uses_run_id_as_span(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushDeepAgentHandler(fake_sync_client, "ch_x", mode="sync")
        run_id = uuid.uuid4()
        h.on_chain_start({"name": "chain"}, {}, run_id=run_id)
        call = fake_sync_client.events.calls[0]
        assert call["span_id"] == str(run_id)

    def test_subagent_emits_handoff(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushDeepAgentHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_tool_start({"name": "task"}, "spawn child", run_id=uuid.uuid4())
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "subagent.spawn"
        assert call["event_type"].value == "agent.handoff"

    def test_int_channel_id_warns(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            AxonPushDeepAgentHandler(fake_sync_client, 7, mode="sync")


class TestAsyncHandler:
    async def test_chain_start_via_background(self, fake_async_client: FakeAsyncClient) -> None:
        h = AsyncAxonPushDeepAgentHandler(fake_async_client, "ch_x", mode="background")
        await h.on_chain_start({"name": "x"}, {}, run_id=uuid.uuid4())
        await h.aflush(timeout=1.0)
        assert len(fake_async_client.events.calls) == 1
        await h.aclose()


class TestFactory:
    def test_picks_sync(self, fake_sync_client: FakeSyncClient) -> None:
        h = get_deepagent_handler(fake_sync_client, "ch_x", mode="sync")
        assert isinstance(h, AxonPushDeepAgentHandler)
