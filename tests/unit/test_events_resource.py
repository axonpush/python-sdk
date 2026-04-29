"""Unit tests for EventsResource — verifies the exact request shape sent to
``POST /event``, the trace_id auto-generation behavior, the model parsing,
and the list endpoint.
"""
from __future__ import annotations

import json

import httpx
import pytest

from axonpush import AxonPush, EventType

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _success_response(**overrides):
    base = {
        "id": 1,
        "identifier": "x",
        "payload": {},
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

    def test_fail_open_sentinel_distinct_from_204_response(self, mock_router):
        """``events.publish()`` uses ``_is_fail_open()`` to detect the
        fail-open sentinel and short-circuit to ``None``. A real 204 (or empty
        200) response from the backend ALSO yields ``None`` from the transport
        layer — but the sentinel check (``data is _FAIL_OPEN_SENTINEL``) is an
        identity check, so a real ``None`` won't trigger short-circuit. It
        falls through to ``Event.model_validate(None)``, which raises a
        Pydantic ValidationError.

        This test pins the current behavior so a future refactor that
        accidentally treats ``None`` like the sentinel (and silently swallows
        a 204) is loud, not silent. **This is a real SDK quirk worth
        documenting** — if the backend ever returns 204 here, the SDK will
        crash. Worth opening an issue against axonpush-python.
        """
        from pydantic import ValidationError as PydValidationError

        mock_router.post("/event").mock(return_value=httpx.Response(204))
        with AxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
        ) as c:
            with pytest.raises(PydValidationError):
                c.events.publish("x", {}, channel_id=5)


class TestPublishResponseParsing:
    def test_parses_event_with_camelcase_aliases(self, mock_router):
        """Legacy synchronous-write response shape: backend returns the full
        Event with a DB-assigned ``id``. SDK must parse every field."""
        mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 99,
                    "identifier": "boot",
                    "payload": {"step": 1},
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

    def test_parses_async_ingest_queued_response(self, mock_router):
        """Default async-ingest response shape (v0.0.7+): backend returns
        ``{identifier, queued: true, createdAt, environmentId}`` with no
        ``id``. ``Event.id`` must parse as ``None`` and ``Event.queued`` as
        ``True``. Pins the new default behavior — a regression that re-makes
        ``id`` required would break every publisher."""
        mock_router.post("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "identifier": "boot",
                    "queued": True,
                    "createdAt": "2026-04-21T10:00:00Z",
                    "environmentId": 7,
                },
            )
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            event = c.events.publish("boot", {}, channel_id=5)
        assert event is not None
        assert event.id is None
        assert event.queued is True
        assert event.identifier == "boot"
        assert event.environment_id == 7


class TestEnvironment:
    def test_client_environment_header_sent(self, mock_router):
        """Constructor ``environment=`` must reach the wire as
        ``X-Axonpush-Environment`` on every request."""
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            environment="production",
        ) as c:
            c.events.publish("x", {}, channel_id=5)
        assert route.calls.last.request.headers["x-axonpush-environment"] == "production"

    def test_no_environment_header_when_unset(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.publish("x", {}, channel_id=5)
        assert "x-axonpush-environment" not in route.calls.last.request.headers

    def test_per_call_environment_in_request_body(self, mock_router):
        """Per-call ``environment=`` on publish() overrides the client default
        and travels in the request body (not the header)."""
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            environment="production",
        ) as c:
            c.events.publish("x", {}, channel_id=5, environment="eval")
        assert _request_body(route)["environment"] == "eval"

    def test_client_environment_context_manager(self, mock_router):
        """``with client.environment("eval"):`` overrides per-call env for the
        block and restores the client default on exit."""
        route = mock_router.post("/event").mock(return_value=_success_response())
        with AxonPush(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            environment="production",
        ) as c:
            with c.environment("eval"):
                c.events.publish("inside", {}, channel_id=5)
            c.events.publish("outside", {}, channel_id=5)

        bodies = [json.loads(call.request.content) for call in route.calls]
        inside = next(b for b in bodies if b["identifier"] == "inside")
        outside = next(b for b in bodies if b["identifier"] == "outside")
        assert inside["environment"] == "eval"
        assert outside["environment"] == "production"


class TestList:
    def test_list_endpoint_path(self, mock_router):
        route = mock_router.get("/event").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            result = c.events.list(5)
        assert route.called
        assert route.calls.last.request.url.params.get("channelId") == "5"
        assert result == []

    def test_list_typed_filters_in_query_string(self, mock_router):
        route = mock_router.get("/event").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.list(
                5,
                event_type="agent.error",
                agent_id="bot",
                trace_id="tr_x",
                cursor="cur_42",
                limit=50,
            )
        params = route.calls.last.request.url.params
        assert params.get("channelId") == "5"
        assert params.get("eventType") == "agent.error"
        assert params.get("agentId") == "bot"
        assert params.get("traceId") == "tr_x"
        assert params.get("cursor") == "cur_42"
        assert params.get("limit") == "50"

    def test_list_payload_filter_json_encoded(self, mock_router):
        route = mock_router.get("/event").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.list(5, payload_filter={"status": {"$eq": "ok"}})
        params = route.calls.last.request.url.params
        assert params.get("payloadFilter") == '{"status": {"$eq": "ok"}}'

    def test_list_parses_envelope_data_field(self, mock_router):
        """Backend may wrap the result list in {data: [...]} — list() unwraps."""
        mock_router.get("/event").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 1,
                            "identifier": "a",
                            "payload": {},
                            "eventType": "custom",
                        },
                        {
                            "id": 2,
                            "identifier": "b",
                            "payload": {},
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
        mock_router.get("/event").mock(side_effect=httpx.ConnectError("refused"))
        with AxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
        ) as c:
            result = c.events.list(5)
        assert result == []


class TestSearch:
    def test_search_endpoint_path(self, mock_router):
        route = mock_router.get("/event/search").mock(
            return_value=httpx.Response(200, json=[])
        )
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            c.events.search(channel_id=5, event_type=["agent.start", "agent.end"])
        params = route.calls.last.request.url.params
        assert params.get("channelId") == "5"
        assert params.get("eventType") == "agent.start,agent.end"
