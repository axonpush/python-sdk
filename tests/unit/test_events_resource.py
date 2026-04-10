"""Unit tests for EventsResource — verifies the exact request shape sent to
``POST /event``, the trace_id auto-generation behavior, the model parsing,
and the list endpoint.
"""
from __future__ import annotations

import json

import httpx

from axonpush import AxonPush, EventType

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _success_response(**overrides):
    base = {
        "id": 1,
        "identifier": "x",
        "payload": {},
        "channel_id": 5,
        "eventType": "custom",
    }
    base.update(overrides)
    return httpx.Response(200, json=base)


def _request_body(route) -> dict:
    return json.loads(route.calls.last.request.content)


class TestPublishRequestBody:
    def test_minimal_request_body(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish("greet", {"hello": "world"}, channel_id=5)

        body = _request_body(route)
        assert body["identifier"] == "greet"
        assert body["payload"] == {"hello": "world"}
        assert body["channel_id"] == 5
        # trace_id auto-populated when not passed (camelCased on the wire)
        assert "traceId" in body
        assert body["traceId"].startswith("tr_")

    def test_camelcase_field_aliases(self, mock_router):
        """All snake_case kwargs must be sent as camelCase on the wire so the
        NestJS backend's class-validator accepts them."""
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish(
                "greet",
                {},
                channel_id=5,
                agent_id="bot",
                trace_id="tr_abc1234567890000",
                span_id="sp_001",
                parent_event_id=42,
                event_type=EventType.AGENT_TOOL_CALL_START,
                metadata={"k": "v"},
            )

        body = _request_body(route)
        assert body["agentId"] == "bot"
        assert body["traceId"] == "tr_abc1234567890000"
        assert body["spanId"] == "sp_001"
        assert body["parentEventId"] == 42
        assert body["eventType"] == "agent.tool_call.start"
        assert body["metadata"] == {"k": "v"}
        # snake_case keys must NOT also appear (would confuse Nest)
        assert "agent_id" not in body
        assert "trace_id" not in body
        assert "span_id" not in body
        assert "parent_event_id" not in body
        assert "event_type" not in body

    def test_string_event_type_coerced_to_enum(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish(
                "x", {}, channel_id=5, event_type="agent.handoff"
            )
        assert _request_body(route)["eventType"] == "agent.handoff"

    def test_explicit_trace_id_overrides_auto(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_success_response())
        explicit = "tr_my_explicit_trace_xx"
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish("x", {}, channel_id=5, trace_id=explicit)
        assert _request_body(route)["traceId"] == explicit

    def test_none_optional_fields_excluded(self, mock_router):
        """The Pydantic model uses ``exclude_none=True``, so optional fields
        we didn't set must not appear in the request body."""
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish("x", {}, channel_id=5)
        body = _request_body(route)
        for excluded in ("agentId", "spanId", "parentEventId", "eventType", "metadata"):
            assert excluded not in body

    def test_publish_returns_none_on_fail_open(self, mock_router):
        mock_router.post("/event").mock(side_effect=httpx.ConnectError("refused"))
        with AxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
        ) as c:
            result = c.events.publish("x", {}, channel_id=5)
        assert result is None


class TestPublishResponseParsing:
    def test_parses_event_with_camelcase_aliases(self, mock_router):
        mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 99,
                    "identifier": "boot",
                    "payload": {"step": 1},
                    "channel_id": 5,
                    "agentId": "orchestrator",
                    "traceId": "tr_xyz",
                    "spanId": "sp_001",
                    "eventType": "agent.start",
                    "metadata": {"src": "test"},
                },
            )
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            event = c.events.publish("boot", {"step": 1}, channel_id=5)
        assert event is not None
        assert event.id == 99
        assert event.agent_id == "orchestrator"
        assert event.trace_id == "tr_xyz"
        assert event.span_id == "sp_001"
        assert event.event_type == EventType.AGENT_START
        assert event.metadata == {"src": "test"}


class TestList:
    def test_list_endpoint_path(self, mock_router):
        route = mock_router.get("/event/5/list").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            result = c.events.list(5)
        assert route.called
        assert result == []

    def test_list_pagination_params(self, mock_router):
        route = mock_router.get("/event/5/list").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.list(5, page=2, limit=50)
        req = route.calls.last.request
        assert req.url.params.get("page") == "2"
        assert req.url.params.get("limit") == "50"

    def test_list_parses_envelope_data_field(self, mock_router):
        """Backend may wrap the result list in {data: [...]} — list() unwraps."""
        mock_router.get("/event/5/list").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 1,
                            "identifier": "a",
                            "payload": {},
                            "channel_id": 5,
                            "eventType": "custom",
                        },
                        {
                            "id": 2,
                            "identifier": "b",
                            "payload": {},
                            "channel_id": 5,
                            "eventType": "custom",
                        },
                    ]
                },
            )
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            events = c.events.list(5)
        assert len(events) == 2
        assert events[0].identifier == "a"
        assert events[1].identifier == "b"

    def test_list_returns_empty_on_fail_open(self, mock_router):
        mock_router.get("/event/5/list").mock(side_effect=httpx.ConnectError("refused"))
        with AxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
        ) as c:
            result = c.events.list(5)
        assert result == []
