"""Unit tests for the ``Events`` / ``AsyncEvents`` resources.

These tests don't open a real HTTP connection. They instantiate the resource
with a fake ``_invoke``-shaped client and assert the body that would be
shipped to the backend (the generated DTO instance) matches the user's
inputs.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import pytest

from axonpush._internal.api.api.event import (
    event_controller_create_event as _create_op,
    event_controller_list_events as _list_op,
)
from axonpush._internal.api.api.events import (
    events_search_controller_search as _search_op,
)
from axonpush._internal.api.models import (
    CreateEventDto,
    CreateEventDtoEventType,
    EventIngestResponseDto,
)
from axonpush._internal.api.types import UNSET
from axonpush.resources.events import AsyncEvents, Events

CHANNEL_ID = "11111111-1111-1111-1111-111111111111"


def _ingest_response(**overrides: Any) -> EventIngestResponseDto:
    base = {
        "event_id": "ev_1",
        "identifier": "x",
        "dedup_key": "x",
        "created_at": "2026-01-01T00:00:00Z",
        "queued": True,
    }
    base.update(overrides)
    return EventIngestResponseDto(**base)


class FakeSyncClient:
    """Captures the op + kwargs the resource passes to ``_invoke``."""

    def __init__(self, return_value: Any = None) -> None:
        self.calls: list[tuple[Callable[..., Any], dict[str, Any]]] = []
        self.return_value = return_value

    def _invoke(self, op: Callable[..., Any], /, **kwargs: Any) -> Any:
        self.calls.append((op, kwargs))
        return self.return_value


class FakeAsyncClient:
    def __init__(self, return_value: Any = None) -> None:
        self.calls: list[tuple[Callable[..., Awaitable[Any]], dict[str, Any]]] = []
        self.return_value = return_value

    async def _invoke(self, op: Callable[..., Awaitable[Any]], /, **kwargs: Any) -> Any:
        self.calls.append((op, kwargs))
        return self.return_value


class TestPublishBody:
    def test_minimal_publish_assembles_dto(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        result = events.publish("greet", {"hello": "world"}, channel_id=CHANNEL_ID)

        assert isinstance(result, EventIngestResponseDto)
        op, kwargs = fake.calls[0]
        assert op is _create_op
        body = kwargs["body"]
        assert isinstance(body, CreateEventDto)
        assert body.identifier == "greet"
        assert body.channel_id == CHANNEL_ID
        assert body.payload.additional_properties == {"hello": "world"}
        # trace_id auto-generated when none was provided (UUID4 string)
        assert isinstance(body.trace_id, str)
        assert len(body.trace_id) == 36 and body.trace_id.count("-") == 4
        # Optional fields default to UNSET
        assert body.agent_id is UNSET
        assert body.span_id is UNSET
        assert body.parent_event_id is UNSET
        assert body.metadata is UNSET
        assert body.environment is UNSET

    def test_explicit_trace_id_is_passed_through(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        events.publish("x", {}, channel_id=CHANNEL_ID, trace_id="tr_explicit")

        body = fake.calls[0][1]["body"]
        assert body.trace_id == "tr_explicit"

    def test_string_event_type_is_coerced_to_enum(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        events.publish("x", {}, channel_id=CHANNEL_ID, event_type="agent.handoff")

        body = fake.calls[0][1]["body"]
        assert body.event_type is CreateEventDtoEventType.AGENT_HANDOFF

    def test_enum_event_type_is_passed_through(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        events.publish("x", {}, channel_id=CHANNEL_ID, event_type=CreateEventDtoEventType.AGENT_END)

        body = fake.calls[0][1]["body"]
        assert body.event_type is CreateEventDtoEventType.AGENT_END

    def test_metadata_wrapped_into_dto(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        events.publish("x", {}, channel_id=CHANNEL_ID, metadata={"src": "test"})

        body = fake.calls[0][1]["body"]
        assert body.metadata is not UNSET
        assert body.metadata.additional_properties == {"src": "test"}

    def test_all_tracing_fields_propagate(self) -> None:
        fake = FakeSyncClient(return_value=_ingest_response())
        events = Events(fake)
        events.publish(
            "x",
            {},
            channel_id=CHANNEL_ID,
            agent_id="bot",
            trace_id="tr_fixed",
            span_id="sp_fixed",
            parent_event_id="ev_parent",
            environment="staging",
        )

        body = fake.calls[0][1]["body"]
        assert body.agent_id == "bot"
        assert body.trace_id == "tr_fixed"
        assert body.span_id == "sp_fixed"
        assert body.parent_event_id == "ev_parent"
        assert body.environment == "staging"


class TestList:
    def test_list_calls_list_op_with_channel_id(self) -> None:
        fake = FakeSyncClient(return_value=None)
        events = Events(fake)
        events.list(CHANNEL_ID)

        op, kwargs = fake.calls[0]
        assert op is _list_op
        assert kwargs == {"channel_id": CHANNEL_ID}

    def test_search_calls_search_op_with_no_args(self) -> None:
        fake = FakeSyncClient(return_value=None)
        events = Events(fake)
        events.search()

        op, kwargs = fake.calls[0]
        assert op is _search_op
        assert kwargs == {}


class TestAsyncEvents:
    @pytest.mark.asyncio
    async def test_async_publish_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient(return_value=_ingest_response())
        events = AsyncEvents(fake)
        result = await events.publish("greet", {}, channel_id=CHANNEL_ID)

        assert isinstance(result, EventIngestResponseDto)
        op, kwargs = fake.calls[0]
        assert op is _create_op
        body = kwargs["body"]
        assert isinstance(body, CreateEventDto)
        assert body.identifier == "greet"

    @pytest.mark.asyncio
    async def test_async_list_dispatches_asyncio_op(self) -> None:
        fake = FakeAsyncClient(return_value=None)
        events = AsyncEvents(fake)
        await events.list(CHANNEL_ID)

        op, kwargs = fake.calls[0]
        assert op is _list_op
        assert kwargs == {"channel_id": CHANNEL_ID}
