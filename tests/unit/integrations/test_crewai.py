"""Unit tests for ``AxonPushCrewCallbacks``.

CrewAI doesn't need to be importable for the integration to be tested —
the callback class is plain Python and uses only attribute access on
the step output object.
"""

from __future__ import annotations

import pytest

from axonpush.integrations.crewai import AxonPushCrewCallbacks

from .conftest import FakeSyncClient


class _StepOutput:
    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCrewCallbacks:
    def test_on_crew_start(self, fake_sync_client: FakeSyncClient) -> None:
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_crew_start()
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "crew.start"
        assert call["event_type"].value == "agent.start"
        assert call["channel_id"] == "ch_x"

    def test_on_step_with_tool(self, fake_sync_client: FakeSyncClient) -> None:
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_step(
            _StepOutput(
                agent="researcher",
                tool="search",
                tool_input="ai agents",
                result="found",
            )
        )
        ids = [c["identifier"] for c in fake_sync_client.events.calls]
        assert "tool.search.start" in ids
        assert "tool.search.end" in ids

    def test_on_step_thought(self, fake_sync_client: FakeSyncClient) -> None:
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_step(_StepOutput(agent="r", tool=None, thought="thinking..."))
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "agent.step"
        assert call["event_type"].value == "agent.message"
        assert call["payload"]["thought"] == "thinking..."

    def test_on_task_complete(self, fake_sync_client: FakeSyncClient) -> None:
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_task_complete(_StepOutput(description="research", __str__=None))
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "task.complete"
        assert call["event_type"].value == "agent.end"

    def test_on_crew_end(self, fake_sync_client: FakeSyncClient) -> None:
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_crew_end("done")
        assert fake_sync_client.events.calls[0]["identifier"] == "crew.end"

    def test_publish_failure_swallowed(self, fake_sync_client: FakeSyncClient) -> None:
        fake_sync_client.events.exception = RuntimeError("nope")
        cb = AxonPushCrewCallbacks(fake_sync_client, "ch_x", mode="sync")
        cb.on_crew_start()  # must not raise

    def test_int_channel_id_warns(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            cb = AxonPushCrewCallbacks(fake_sync_client, 1, mode="sync")
        cb.on_crew_start()
        assert fake_sync_client.events.calls[0]["channel_id"] == "1"
