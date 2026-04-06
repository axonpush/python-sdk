"""Tests for the Deep Agents integration callback handler.

These tests exercise the handler's event classification and publishing logic
by calling callback methods directly and verifying the events.publish calls.

Requires: ``uv sync --extra deepagents``
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.outputs import LLMResult

from axonpush.integrations.deepagents import AxonPushDeepAgentHandler
from axonpush.models.events import EventType


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.events.publish.return_value = MagicMock(id=1)
    return client


@pytest.fixture()
def handler(mock_client):
    return AxonPushDeepAgentHandler(
        mock_client,
        channel_id=42,
        agent_id="test-agent",
        trace_id="tr_test1234567890",
    )


class TestDeepAgentToolClassification:
    """Verify that Deep Agent built-in tools get enriched identifiers."""

    def test_planning_tool_start(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start(
            {"name": "write_todos"},
            '{"todos": ["step 1", "step 2"]}',
            run_id=run_id,
        )
        mock_client.events.publish.assert_called_once()
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "planning.update"
        assert kw.kwargs["event_type"] == EventType.AGENT_TOOL_CALL_START
        assert kw.kwargs["payload"]["tool_name"] == "write_todos"

    def test_planning_tool_end(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_end("done", run_id=run_id, name="write_todos")
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "planning.complete"
        assert kw.kwargs["event_type"] == EventType.AGENT_TOOL_CALL_END

    def test_subagent_tool_start(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start(
            {"name": "task"},
            '{"description": "research sub-task"}',
            run_id=run_id,
        )
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "subagent.spawn"
        assert kw.kwargs["event_type"] == EventType.AGENT_HANDOFF

    def test_subagent_tool_end(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_end("sub-result", run_id=run_id, name="task")
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "subagent.complete"
        assert kw.kwargs["event_type"] == EventType.AGENT_TOOL_CALL_END

    def test_filesystem_read_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "read_file"}, "path/to/file", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.read"

    def test_filesystem_write_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "write_file"}, "content", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.write"

    def test_filesystem_edit_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "edit_file"}, "diff", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.write"

    def test_filesystem_ls_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "ls"}, ".", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.read"

    def test_filesystem_glob_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "glob"}, "**/*.py", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.read"

    def test_filesystem_grep_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "grep"}, "pattern", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "filesystem.read"

    def test_sandbox_execute_tool(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "execute"}, "ls -la", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "sandbox.execute"

    def test_unknown_tool_falls_back(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_start({"name": "custom_tool"}, "input", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "tool.custom_tool.start"
        assert kw.kwargs["event_type"] == EventType.AGENT_TOOL_CALL_START

    def test_unknown_tool_end_falls_back(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_end("output", run_id=run_id, name="custom_tool")
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "tool.end"
        assert kw.kwargs["event_type"] == EventType.AGENT_TOOL_CALL_END


class TestDeepAgentChainLifecycle:
    """Verify chain start/end/error callbacks."""

    def test_chain_start(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_start(
            {"name": "DeepAgent"}, {"messages": []}, run_id=run_id
        )
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "chain.start"
        assert kw.kwargs["event_type"] == EventType.AGENT_START
        assert kw.kwargs["payload"]["chain_type"] == "DeepAgent"

    def test_chain_end(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_end({"output": "result"}, run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "chain.end"
        assert kw.kwargs["event_type"] == EventType.AGENT_END

    def test_chain_error(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_error(ValueError("test error"), run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "chain.error"
        assert kw.kwargs["event_type"] == EventType.AGENT_ERROR
        assert kw.kwargs["payload"]["error"] == "test error"
        assert kw.kwargs["payload"]["error_type"] == "ValueError"


class TestDeepAgentLLMLifecycle:
    """Verify LLM start/end/token callbacks."""

    def test_llm_start(self, handler, mock_client):
        run_id = uuid4()
        handler.on_llm_start(
            {"name": "gpt-4o"}, ["prompt1", "prompt2"], run_id=run_id
        )
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "llm.start"
        assert kw.kwargs["event_type"] == EventType.AGENT_START
        assert kw.kwargs["payload"]["model"] == "gpt-4o"
        assert kw.kwargs["payload"]["prompt_count"] == 2

    def test_llm_end(self, handler, mock_client):
        run_id = uuid4()
        result = LLMResult(generations=[[], []])
        handler.on_llm_end(result, run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "llm.end"
        assert kw.kwargs["event_type"] == EventType.AGENT_END
        assert kw.kwargs["payload"]["generations"] == 2

    def test_llm_new_token(self, handler, mock_client):
        run_id = uuid4()
        handler.on_llm_new_token("Hello", run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "llm.token"
        assert kw.kwargs["event_type"] == EventType.AGENT_LLM_TOKEN
        assert kw.kwargs["payload"]["token"] == "Hello"


class TestDeepAgentMetadata:
    """Verify metadata, tracing, and framework identification."""

    def test_framework_metadata(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_start({"name": "test"}, {}, run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["metadata"]["framework"] == "deepagents"

    def test_trace_id_propagation(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_start({"name": "test"}, {}, run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["trace_id"] == "tr_test1234567890"

    def test_span_id_sequential(self, handler, mock_client):
        run_id = uuid4()
        handler.on_chain_start({"name": "a"}, {}, run_id=run_id)
        handler.on_chain_end({}, run_id=run_id)

        calls = mock_client.events.publish.call_args_list
        span1 = calls[0].kwargs["span_id"]
        span2 = calls[1].kwargs["span_id"]
        assert span1.endswith("_0001")
        assert span2.endswith("_0002")

    def test_run_id_in_metadata(self, handler, mock_client):
        run_id = uuid4()
        parent_id = uuid4()
        handler.on_chain_start(
            {"name": "test"}, {}, run_id=run_id, parent_run_id=parent_id
        )
        meta = mock_client.events.publish.call_args.kwargs["metadata"]
        assert meta["langchain_run_id"] == str(run_id)
        assert meta["langchain_parent_run_id"] == str(parent_id)

    def test_custom_metadata_preserved(self, mock_client):
        h = AxonPushDeepAgentHandler(
            mock_client,
            channel_id=1,
            metadata={"custom_key": "custom_val"},
        )
        h.on_chain_start({"name": "test"}, {}, run_id=uuid4())
        meta = mock_client.events.publish.call_args.kwargs["metadata"]
        assert meta["custom_key"] == "custom_val"
        assert meta["framework"] == "deepagents"

    def test_tool_error(self, handler, mock_client):
        run_id = uuid4()
        handler.on_tool_error(RuntimeError("file not found"), run_id=run_id)
        kw = mock_client.events.publish.call_args
        assert kw.kwargs["identifier"] == "tool.error"
        assert kw.kwargs["event_type"] == EventType.AGENT_ERROR
