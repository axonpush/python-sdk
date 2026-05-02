"""Unit tests for the OpenAI Agents SDK hooks."""
from __future__ import annotations

import pytest

pytest.importorskip("agents")

from axonpush.integrations.openai_agents import AxonPushRunHooks  # noqa: E402

from .conftest import FakeAsyncClient  # noqa: E402


class _FakeAgent:
    def __init__(self, name: str, model: str | None = None) -> None:
        self.name = name
        self.model = model


class _FakeTool:
    def __init__(self, name: str) -> None:
        self.name = name


class _Ctx:
    """Stand-in for ``RunContextWrapper``; the integration just passes it through."""


class TestRunHooks:
    async def test_on_agent_start(
        self, fake_async_client: FakeAsyncClient
    ) -> None:
        hooks = AxonPushRunHooks(fake_async_client, "ch_x", mode="background")
        await hooks.on_agent_start(_Ctx(), _FakeAgent("planner", "gpt-4"))
        await hooks.flush(timeout=1.0)
        call = fake_async_client.events.calls[0]
        assert call["identifier"] == "agent.run.start"
        assert call["event_type"].value == "agent.start"
        assert call["agent_id"] == "planner"
        assert call["payload"]["model"] == "gpt-4"
        await hooks.close()

    async def test_on_tool_start_and_end(
        self, fake_async_client: FakeAsyncClient
    ) -> None:
        hooks = AxonPushRunHooks(fake_async_client, "ch_x", mode="background")
        agent = _FakeAgent("a")
        tool = _FakeTool("search")
        await hooks.on_tool_start(_Ctx(), agent, tool)
        await hooks.on_tool_end(_Ctx(), agent, tool, "result")
        await hooks.flush(timeout=1.0)
        ids = [c["identifier"] for c in fake_async_client.events.calls]
        assert "tool.search.start" in ids
        assert "tool.search.end" in ids
        await hooks.close()

    async def test_on_handoff(
        self, fake_async_client: FakeAsyncClient
    ) -> None:
        hooks = AxonPushRunHooks(fake_async_client, "ch_x", mode="background")
        await hooks.on_handoff(_Ctx(), _FakeAgent("a"), _FakeAgent("b"))
        await hooks.flush(timeout=1.0)
        call = fake_async_client.events.calls[0]
        assert call["event_type"].value == "agent.handoff"
        assert call["payload"]["from_agent"] == "a"
        assert call["payload"]["to_agent"] == "b"
        await hooks.close()

    async def test_int_channel_id_warns(
        self, fake_async_client: FakeAsyncClient
    ) -> None:
        with pytest.warns(DeprecationWarning):
            hooks = AxonPushRunHooks(fake_async_client, 99, mode="background")
        await hooks.close()
