"""Unit tests for the Anthropic SDK tracer."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("anthropic")

from axonpush.integrations.anthropic import AxonPushAnthropicTracer  # noqa: E402

from .conftest import FakeAsyncClient, FakeSyncClient  # noqa: E402


class _TextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class _ToolUseBlock:
    type = "tool_use"

    def __init__(self, name: str, id: str, inp: dict) -> None:
        self.name = name
        self.id = id
        self.input = inp


class _Usage:
    def __init__(self, in_t: int, out_t: int) -> None:
        self.input_tokens = in_t
        self.output_tokens = out_t


class _Response:
    def __init__(self, content: list, usage: _Usage | None = None) -> None:
        self.content = content
        self.usage = usage
        self.model = "claude-test"
        self.stop_reason = "end_turn"


class _FakeAnthropicMessages:
    def __init__(self, response: _Response) -> None:
        self._response = response
        self.last_kwargs: dict | None = None

    def create(self, **kwargs: Any) -> _Response:
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicAsyncMessages:
    def __init__(self, response: _Response) -> None:
        self._response = response
        self.last_kwargs: dict | None = None

    async def create(self, **kwargs: Any) -> _Response:
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropic:
    def __init__(self, response: _Response) -> None:
        self.messages = _FakeAnthropicMessages(response)


class _FakeAnthropicAsync:
    def __init__(self, response: _Response) -> None:
        self.messages = _FakeAnthropicAsyncMessages(response)


class TestAnthropicTracer:
    def test_create_message_emits_start_then_response(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        tracer = AxonPushAnthropicTracer(fake_sync_client, "ch_x", mode="sync")
        response = _Response([_TextBlock("hi")], usage=_Usage(in_t=10, out_t=5))
        anthropic_client = _FakeAnthropic(response)
        result = tracer.create_message(
            anthropic_client, model="claude-3", messages=[{"role": "user", "content": "x"}]
        )
        assert result is response
        identifiers = [c["identifier"] for c in fake_sync_client.events.calls]
        assert "conversation.turn" in identifiers
        assert "agent.usage" in identifiers
        assert "agent.response" in identifiers
        usage_call = next(
            c for c in fake_sync_client.events.calls if c["identifier"] == "agent.usage"
        )
        assert usage_call["payload"]["input_tokens"] == 10
        assert usage_call["payload"]["output_tokens"] == 5

    def test_tool_use_block_emits_tool_call_start(self, fake_sync_client: FakeSyncClient) -> None:
        tracer = AxonPushAnthropicTracer(fake_sync_client, "ch_x", mode="sync")
        response = _Response([_ToolUseBlock("search", "tool_1", {"q": "x"})], usage=None)
        tracer.create_message(_FakeAnthropic(response), model="claude-3", messages=[])
        ids = [c["identifier"] for c in fake_sync_client.events.calls]
        assert "tool.search.start" in ids

    def test_send_tool_result(self, fake_sync_client: FakeSyncClient) -> None:
        tracer = AxonPushAnthropicTracer(fake_sync_client, "ch_x", mode="sync")
        tracer.send_tool_result("tool_1", {"x": 1})
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "tool.result"
        assert call["event_type"].value == "agent.tool_call.end"
        assert call["payload"]["tool_use_id"] == "tool_1"

    async def test_acreate_message(self, fake_async_client: FakeAsyncClient) -> None:
        tracer = AxonPushAnthropicTracer(fake_async_client, "ch_x", mode="background")
        response = _Response([_TextBlock("hi")], usage=_Usage(1, 2))
        await tracer.acreate_message(_FakeAnthropicAsync(response), model="claude-3", messages=[])
        await tracer.aflush(timeout=1.0)
        ids = [c["identifier"] for c in fake_async_client.events.calls]
        assert "conversation.turn" in ids
        assert "agent.usage" in ids
        await tracer.aclose()

    def test_int_channel_id_warns(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            AxonPushAnthropicTracer(fake_sync_client, 99, mode="sync")
