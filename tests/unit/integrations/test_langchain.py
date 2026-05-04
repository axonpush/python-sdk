"""Unit tests for the LangChain callback handlers."""

from __future__ import annotations

import uuid

import pytest

pytest.importorskip("langchain_core")

from axonpush.integrations.langchain import (  # noqa: E402
    AsyncAxonPushCallbackHandler,
    AxonPushCallbackHandler,
    get_langchain_handler,
)

from .conftest import FakeAsyncClient, FakeSyncClient  # noqa: E402


class TestSyncHandler:
    def test_chain_start_emits_agent_start(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        run_id = uuid.uuid4()
        h.on_chain_start({"name": "MyChain"}, {"q": "hi"}, run_id=run_id)
        assert len(fake_sync_client.events.calls) == 1
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "chain.start"
        assert call["event_type"].value == "agent.start"
        assert call["channel_id"] == "ch_x"
        assert call["span_id"] == str(run_id)
        assert call["metadata"]["langchain_run_id"] == str(run_id)

    def test_parent_run_id_becomes_parent_event_id(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        run_id = uuid.uuid4()
        parent_run_id = uuid.uuid4()
        h.on_chain_start({"name": "Sub"}, {}, run_id=run_id, parent_run_id=parent_run_id)
        call = fake_sync_client.events.calls[0]
        assert call["parent_event_id"] == str(parent_run_id)
        assert call["metadata"]["langchain_parent_run_id"] == str(parent_run_id)

    def test_chain_error_emits_agent_error(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_chain_error(ValueError("nope"), run_id=uuid.uuid4())
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "chain.error"
        assert call["event_type"].value == "agent.error"
        assert call["payload"]["error_type"] == "ValueError"
        assert call["payload"]["error"] == "nope"

    def test_tool_start_emits_tool_call(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_tool_start({"name": "search"}, "q", run_id=uuid.uuid4())
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "tool.search.start"
        assert call["event_type"].value == "agent.tool_call.start"

    def test_llm_token_event(self, fake_sync_client: FakeSyncClient) -> None:
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_llm_new_token("hello", run_id=uuid.uuid4())
        assert fake_sync_client.events.calls[0]["event_type"].value == "agent.llm.token"

    def test_publish_failure_swallowed(self, fake_sync_client: FakeSyncClient) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_chain_start({"name": "x"}, {}, run_id=uuid.uuid4())

    def test_int_channel_id_warns(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            h = AxonPushCallbackHandler(fake_sync_client, 99, mode="sync")
        h.on_chain_start({"name": "x"}, {}, run_id=uuid.uuid4())
        assert fake_sync_client.events.calls[0]["channel_id"] == "99"

    def test_chain_start_falls_back_to_kwargs_name_for_langgraph(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        # LangGraph passes serialized={} and exposes the node identity via
        # kwargs["name"] + kwargs["metadata"]["langgraph_node"]. The SDK must
        # surface that — pre-0.0.13 it emitted "unknown".
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_chain_start(
            {},
            {"messages": []},
            run_id=uuid.uuid4(),
            name="researcher",
            metadata={"langgraph_node": "researcher", "langgraph_step": 3},
            tags=["graph:my_graph"],
        )
        call = fake_sync_client.events.calls[0]
        assert call["payload"]["chain_type"] == "researcher"
        assert call["metadata"]["langgraph_node"] == "researcher"
        assert call["metadata"]["langgraph_step"] == 3
        assert call["metadata"]["tags"] == ["graph:my_graph"]

    def test_llm_start_uses_invocation_params_model(
        self, fake_sync_client: FakeSyncClient
    ) -> None:
        # serialized.name is the wrapper class ("ChatOpenAI"); the real model
        # id is in invocation_params (or serialized.kwargs.model). Pre-0.0.13
        # the trace would just show "ChatOpenAI".
        h = AxonPushCallbackHandler(fake_sync_client, "ch_x", mode="sync")
        h.on_llm_start(
            {"name": "ChatOpenAI", "kwargs": {"model_name": "gpt-4o-mini"}},
            ["hi"],
            run_id=uuid.uuid4(),
            invocation_params={"model": "gpt-4o-mini-2024-07-18"},
        )
        call = fake_sync_client.events.calls[0]
        assert call["payload"]["model"] == "gpt-4o-mini-2024-07-18"


class TestAsyncHandler:
    async def test_chain_start_via_background_publisher(
        self, fake_async_client: FakeAsyncClient
    ) -> None:
        h = AsyncAxonPushCallbackHandler(fake_async_client, "ch_x", mode="background")
        run_id = uuid.uuid4()
        await h.on_chain_start({"name": "X"}, {}, run_id=run_id)
        await h.aflush(timeout=1.0)
        assert len(fake_async_client.events.calls) == 1
        assert fake_async_client.events.calls[0]["span_id"] == str(run_id)
        await h.aclose()

    async def test_parent_run_id_propagated_async(self, fake_async_client: FakeAsyncClient) -> None:
        h = AsyncAxonPushCallbackHandler(fake_async_client, "ch_x", mode="background")
        parent = uuid.uuid4()
        await h.on_chain_start({"name": "x"}, {}, run_id=uuid.uuid4(), parent_run_id=parent)
        await h.aflush(timeout=1.0)
        assert fake_async_client.events.calls[0]["parent_event_id"] == str(parent)
        await h.aclose()


class TestFactory:
    def test_picks_sync_for_sync_client(self, fake_sync_client: FakeSyncClient) -> None:
        h = get_langchain_handler(fake_sync_client, "ch_x", mode="sync")
        assert isinstance(h, AxonPushCallbackHandler)
