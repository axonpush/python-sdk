"""Async MQTT realtime client tests — aiomqtt is fully mocked."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from axonpush.realtime.mqtt_async import AsyncRealtimeClient


class _FakeAiomqtt:
    """Stand-in for ``aiomqtt.Client``."""

    instances: list["_FakeAiomqtt"] = []
    enter_raises: BaseException | None = None

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.client_id = kwargs.get("identifier")
        self.subscriptions: list[tuple[str, int]] = []
        self.unsubscriptions: list[str] = []
        self.published: list[tuple[str, bytes, int]] = []
        self._messages_queue: asyncio.Queue[Any] = asyncio.Queue()
        _FakeAiomqtt.instances.append(self)

    async def __aenter__(self) -> "_FakeAiomqtt":
        if _FakeAiomqtt.enter_raises is not None:
            raise _FakeAiomqtt.enter_raises
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    @property
    def messages(self) -> Any:
        async def _gen() -> Any:
            while True:
                msg = await self._messages_queue.get()
                if msg is None:
                    return
                yield msg

        return _gen()

    async def subscribe(self, topic: str, qos: int = 1) -> None:
        self.subscriptions.append((topic, qos))

    async def unsubscribe(self, topic: str) -> None:
        self.unsubscriptions.append(topic)

    async def publish(self, topic: str, payload: Any, qos: int = 1) -> None:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.published.append((topic, payload, qos))

    def push(self, msg: Any) -> None:
        self._messages_queue.put_nowait(msg)

    def close_messages(self) -> None:
        self._messages_queue.put_nowait(None)


class _FakeAiomqttModule:
    Client = _FakeAiomqtt

    class TLSParameters:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


@pytest.fixture(autouse=True)
def reset_fake_aiomqtt() -> None:
    _FakeAiomqtt.instances.clear()
    _FakeAiomqtt.enter_raises = None


@pytest.fixture()
def fake_aiomqtt(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setattr(
        "axonpush.realtime.mqtt_async._import_aiomqtt",
        lambda: _FakeAiomqttModule,
    )
    return _FakeAiomqttModule


def _msg(topic: str, payload: dict[str, Any]) -> Any:
    m = MagicMock()
    m.topic = topic
    m.payload = json.dumps(payload).encode("utf-8")
    return m


@pytest.mark.asyncio
async def test_aconnect_fetches_creds_and_opens_client(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    assert isinstance(rt._mqtt, _FakeAiomqtt)
    assert rt._mqtt.kwargs["hostname"] == "abc-ats.iot.us-east-1.amazonaws.com"
    assert rt._mqtt.kwargs["port"] == 443
    assert rt._mqtt.client_id == "k-test-abc"
    rt._mqtt.close_messages()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_connect_alias_calls_aconnect(fake_async_facade, fake_aiomqtt) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.connect()
    assert rt._mqtt is not None
    rt._mqtt.close_messages()
    await rt.disconnect()


@pytest.mark.asyncio
async def test_subscribe_builds_topic(fake_async_facade, fake_aiomqtt) -> None:
    rt = AsyncRealtimeClient(fake_async_facade, environment="prod")
    await rt.aconnect()
    topic = await rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.error",
        agent_id="bot",
        callback=lambda _msg: None,
    )
    assert topic == "axonpush/org_1/prod/app_1/ch_5/agent_error/bot"
    assert (topic, 1) in rt._mqtt.subscriptions
    rt._mqtt.close_messages()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_publish_serialises_payload(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade, environment="prod")
    await rt.aconnect()
    await rt.publish(
        "ch_5",
        app_id="app_1",
        event_type="agent.message",
        agent_id="bot",
        payload={"identifier": "tick"},
    )
    topic, body, qos = rt._mqtt.published[-1]
    assert topic == "axonpush/org_1/prod/app_1/ch_5/agent_message/bot"
    assert qos == 1
    assert json.loads(body.decode("utf-8")) == {"identifier": "tick"}
    rt._mqtt.close_messages()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_publish_falls_back_to_credential_env_slug(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    await rt.publish(
        "ch_5", app_id="app_1", event_type="custom", payload={"x": 1}
    )
    topic, _b, _q = rt._mqtt.published[-1]
    assert topic == "axonpush/org_1/default/app_1/ch_5/custom/_"
    rt._mqtt.close_messages()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_publish_before_connect_raises(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    with pytest.raises(RuntimeError, match="connect"):
        await rt.publish(
            "ch_5", app_id="app_1", event_type="custom", payload={}
        )


@pytest.mark.asyncio
async def test_subscribe_before_connect_raises(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    with pytest.raises(RuntimeError, match="connect"):
        await rt.subscribe("ch_5", callback=lambda _m: None)


@pytest.mark.asyncio
async def test_async_callback_dispatched(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    received: list[dict[str, Any]] = []

    async def cb(payload: dict[str, Any]) -> None:
        received.append(payload)

    await rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.message",
        callback=cb,
    )
    rt._mqtt.push(
        _msg(
            "axonpush/org_1/default/app_1/ch_5/agent_message/_",
            {"identifier": "tick"},
        )
    )
    rt._mqtt.close_messages()
    if rt._reader_task is not None:
        try:
            await asyncio.wait_for(rt._reader_task, timeout=1.0)
        except asyncio.TimeoutError:
            rt._reader_task.cancel()
    assert received == [{"identifier": "tick"}]
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_sync_callback_also_works(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    received: list[Any] = []
    await rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="custom",
        callback=received.append,
    )
    rt._mqtt.push(
        _msg("axonpush/org_1/default/app_1/ch_5/custom/_", {"x": 1})
    )
    rt._mqtt.close_messages()
    if rt._reader_task is not None:
        try:
            await asyncio.wait_for(rt._reader_task, timeout=1.0)
        except asyncio.TimeoutError:
            rt._reader_task.cancel()
    assert received == [{"x": 1}]
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_failing_callback_does_not_break_reader(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    seen: list[Any] = []

    async def bad(_p: Any) -> None:
        raise RuntimeError("boom")

    await rt.subscribe(
        "ch_5", app_id="app_1", event_type="custom", callback=bad
    )
    await rt.subscribe(
        "ch_5", app_id="app_1", event_type="custom", callback=seen.append
    )
    rt._mqtt.push(
        _msg("axonpush/org_1/default/app_1/ch_5/custom/_", {"x": 1})
    )
    rt._mqtt.close_messages()
    if rt._reader_task is not None:
        try:
            await asyncio.wait_for(rt._reader_task, timeout=1.0)
        except asyncio.TimeoutError:
            rt._reader_task.cancel()
    assert seen == [{"x": 1}]
    assert rt._reader_task is None or rt._reader_task.done()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_invalid_json_dropped(fake_async_facade, fake_aiomqtt) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    received: list[Any] = []
    await rt.subscribe("ch_5", callback=received.append)
    bad = MagicMock()
    bad.topic = "axonpush/org_1/default/app_1/ch_5/custom/_"
    bad.payload = b"not-json"
    rt._mqtt.push(bad)
    rt._mqtt.close_messages()
    if rt._reader_task is not None:
        try:
            await asyncio.wait_for(rt._reader_task, timeout=1.0)
        except asyncio.TimeoutError:
            rt._reader_task.cancel()
    assert received == []
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_aconnect_propagates_broker_error(
    fake_async_facade, fake_aiomqtt
) -> None:
    """If ``__aenter__`` raises, the refresh task is never scheduled —
    fixing the race where a stale-credential refresh could fire after a
    failed reconnect."""
    _FakeAiomqtt.enter_raises = ConnectionError("broker rejected")
    rt = AsyncRealtimeClient(fake_async_facade)
    with pytest.raises(ConnectionError):
        await rt.aconnect()
    assert rt._refresh_task is None


@pytest.mark.asyncio
async def test_adisconnect_cancels_tasks(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    assert rt._refresh_task is not None
    assert rt._reader_task is not None
    await rt.adisconnect()
    assert rt._mqtt is None
    assert rt._refresh_task is None
    assert rt._reader_task is None


@pytest.mark.asyncio
async def test_unsubscribe_removes_handler(
    fake_async_facade, fake_aiomqtt
) -> None:
    rt = AsyncRealtimeClient(fake_async_facade)
    await rt.aconnect()
    topic = await rt.subscribe("ch_5", callback=lambda _m: None)
    await rt.unsubscribe(topic)
    assert topic not in rt._subscriptions
    assert topic in rt._mqtt.unsubscriptions
    rt._mqtt.close_messages()
    await rt.adisconnect()


@pytest.mark.asyncio
async def test_aiomqtt_missing_raises_actionable_import_error(
    fake_async_facade, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> Any:
        raise ImportError("aiomqtt missing")

    monkeypatch.setattr(
        "axonpush.realtime.mqtt_async._import_aiomqtt", _boom
    )
    with pytest.raises(ImportError, match="aiomqtt"):
        AsyncRealtimeClient(fake_async_facade)
