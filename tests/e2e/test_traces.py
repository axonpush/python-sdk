import time
import uuid

import pytest

from axonpush.models import EventDetails, EventType, TraceSummary

pytestmark = pytest.mark.e2e


class TestTraces:
    def _publish_traced_events(self, client, channel):
        trace_id = f"tr_{uuid.uuid4().hex[:16]}"
        client.events.publish(
            "trace_start",
            {"step": "begin"},
            channel_id=channel.id,
            agent_id="tracer",
            trace_id=trace_id,
            event_type=EventType.AGENT_START,
        )
        client.events.publish(
            "trace_tool",
            {"tool": "search"},
            channel_id=channel.id,
            agent_id="tracer",
            trace_id=trace_id,
            event_type=EventType.AGENT_TOOL_CALL_START,
        )
        client.events.publish(
            "trace_end",
            {"step": "finish"},
            channel_id=channel.id,
            agent_id="tracer",
            trace_id=trace_id,
            event_type=EventType.AGENT_END,
        )
        return trace_id

    def test_list_traces(self, client, channel):
        trace_id = self._publish_traced_events(client, channel)
        time.sleep(0.5)
        result = client.traces.list()
        assert result is not None
        assert hasattr(result, "data")
        trace_ids = [t.trace_id for t in result.data]
        assert trace_id in trace_ids

    def test_events_for_trace(self, client, channel):
        trace_id = self._publish_traced_events(client, channel)
        time.sleep(0.5)
        events = client.traces.events(trace_id)
        assert isinstance(events, list)
        assert len(events) >= 3
        assert all(isinstance(e, EventDetails) for e in events)
        assert all(e.trace_id == trace_id for e in events)

    def test_summary(self, client, channel):
        trace_id = self._publish_traced_events(client, channel)
        time.sleep(0.5)
        summary = client.traces.summary(trace_id)
        assert isinstance(summary, TraceSummary)
        assert summary.trace_id == trace_id
        assert summary.event_count >= 3
        assert "tracer" in summary.agents
        assert summary.tool_call_count >= 1

    def test_stats(self, client, channel):
        self._publish_traced_events(client, channel)
        time.sleep(0.5)
        stats = client.traces.stats()
        assert stats is not None
        assert stats.total_events >= 3
