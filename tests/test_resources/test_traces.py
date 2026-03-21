import uuid
import time

from axonpush import EventType
from axonpush.models.events import Event
from axonpush.models.traces import TraceListItem, TraceSummary


class TestTracesResource:
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
        traces = client.traces.list()
        assert isinstance(traces, list)
        assert all(isinstance(t, TraceListItem) for t in traces)
        trace_ids = [t.trace_id for t in traces]
        assert trace_id in trace_ids

    def test_get_events_for_trace(self, client, channel):
        trace_id = self._publish_traced_events(client, channel)
        time.sleep(0.5)
        events = client.traces.get_events(trace_id)
        assert isinstance(events, list)
        assert len(events) >= 3
        assert all(isinstance(e, Event) for e in events)
        assert all(e.trace_id == trace_id for e in events)

    def test_get_summary(self, client, channel):
        trace_id = self._publish_traced_events(client, channel)
        time.sleep(0.5)
        summary = client.traces.get_summary(trace_id)
        assert isinstance(summary, TraceSummary)
        assert summary.trace_id == trace_id
        assert summary.total_events >= 3
        assert "tracer" in summary.agents
        assert summary.tool_call_count >= 1
