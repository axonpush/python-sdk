"""Sync MQTT realtime client tests — paho is fully mocked."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from axonpush.realtime.mqtt import RealtimeClient


class _FakePaho:
    """Stand-in for ``paho.mqtt.client.Client``.

    Records every call. Normally fires ``on_connect`` with ``rc=0`` on
    ``loop_start``; tests can flip ``connack_rc`` or ``never_connack`` to
    exercise failure paths.
    """

    instances: list["_FakePaho"] = []
    connack_rc = 0
    never_connack = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.client_id = kwargs.get("client_id")
        self.transport = kwargs.get("transport")
        self.connect_args: tuple[Any, ...] = ()
        self.ws_options: dict[str, Any] = {}
        self.tls_set_called = False
        self.subscriptions: list[tuple[str, int]] = []
        self.unsubscriptions: list[str] = []
        self.published: list[tuple[str, bytes, int]] = []
        self.on_connect = lambda *a, **k: None
        self.on_disconnect = lambda *a, **k: None
        self.on_message = lambda *a, **k: None
        self.disconnected = False
        _FakePaho.instances.append(self)

    def ws_set_options(self, **kwargs: Any) -> None:
        self.ws_options = kwargs

    def tls_set(self, *args: Any, **kwargs: Any) -> None:
        self.tls_set_called = True

    def connect_async(self, host: str, port: int, keepalive: int = 30) -> None:
        self.connect_args = (host, port, keepalive)

    def loop_start(self) -> None:
        if _FakePaho.never_connack:
            return
        self.on_connect(self, None, {}, _FakePaho.connack_rc)

    def loop_stop(self) -> None:
        pass

    def subscribe(self, topic: str, qos: int = 1) -> None:
        self.subscriptions.append((topic, qos))

    def unsubscribe(self, topic: str) -> None:
        self.unsubscriptions.append(topic)

    def publish(self, topic: str, payload: bytes | str, qos: int = 1) -> None:
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.published.append((topic, payload, qos))

    def disconnect(self) -> None:
        self.disconnected = True


@pytest.fixture(autouse=True)
def reset_fake_paho() -> None:
    _FakePaho.instances.clear()
    _FakePaho.connack_rc = 0
    _FakePaho.never_connack = False


@pytest.fixture()
def fake_paho(monkeypatch: pytest.MonkeyPatch) -> Any:
    fake_module = MagicMock()
    fake_module.Client = _FakePaho
    fake_module.MQTTv311 = 4
    monkeypatch.setattr("axonpush.realtime.mqtt._import_paho", lambda: fake_module)
    return fake_module


def test_connect_fetches_creds_and_starts_loop(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    assert isinstance(rt._mqtt, _FakePaho)
    assert rt._mqtt.connect_args[0] == "abc-ats.iot.us-east-1.amazonaws.com"
    assert rt._mqtt.connect_args[1] == 443
    assert rt._mqtt.ws_options.get("path", "").startswith("/mqtt")
    assert rt._mqtt.tls_set_called
    assert rt._mqtt.client_id == "k-test-abc"
    rt.disconnect()


def test_connect_uses_topic_prefix_from_credentials(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    assert rt.credentials is not None
    assert rt.credentials.topic_prefix == "axonpush/org_1"
    rt.disconnect()


def test_subscribe_builds_topic_and_calls_paho(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade, environment="prod")
    rt.connect()
    rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.error",
        agent_id="bot",
        callback=lambda _msg: None,
    )
    assert (
        "axonpush/org_1/prod/app_1/ch_5/agent_error/bot",
        1,
    ) in rt._mqtt.subscriptions
    rt.disconnect()


def test_subscribe_without_env_uses_plus(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.error",
        agent_id="bot",
        callback=lambda _msg: None,
    )
    assert (
        "axonpush/org_1/+/app_1/ch_5/agent_error/bot",
        1,
    ) in rt._mqtt.subscriptions
    rt.disconnect()


def test_subscribe_returns_topic_filter(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    topic = rt.subscribe("ch_5", callback=lambda _msg: None)
    assert topic == "axonpush/org_1/+/+/ch_5/+/+"
    rt.disconnect()


def test_publish_serialises_payload(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade, environment="prod")
    rt.connect()
    rt.publish(
        "ch_5",
        app_id="app_1",
        event_type="agent.message",
        agent_id="bot",
        payload={"identifier": "tick", "n": 1},
    )
    topic, body, qos = rt._mqtt.published[-1]
    assert topic == "axonpush/org_1/prod/app_1/ch_5/agent_message/bot"
    assert qos == 1
    assert json.loads(body.decode("utf-8")) == {"identifier": "tick", "n": 1}
    rt.disconnect()


def test_publish_falls_back_to_credential_env_slug(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    rt.publish(
        "ch_5",
        app_id="app_1",
        event_type="custom",
        payload={"x": 1},
    )
    topic, _body, _qos = rt._mqtt.published[-1]
    assert topic == "axonpush/org_1/default/app_1/ch_5/custom/_"
    rt.disconnect()


def test_publish_before_connect_raises(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    with pytest.raises(RuntimeError, match="connect"):
        rt.publish("ch_5", app_id="app_1", event_type="custom", payload={})


def test_subscribe_before_connect_raises(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    with pytest.raises(RuntimeError, match="connect"):
        rt.subscribe("ch_5", callback=lambda _msg: None)


def test_callback_receives_decoded_payload(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    received: list[dict[str, Any]] = []
    rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.message",
        agent_id="bot",
        callback=received.append,
    )
    msg = MagicMock()
    msg.topic = "axonpush/org_1/default/app_1/ch_5/agent_message/bot"
    msg.payload = json.dumps({"identifier": "tick", "n": 1}).encode("utf-8")
    rt._on_message(rt._mqtt, None, msg)
    assert received == [{"identifier": "tick", "n": 1}]
    rt.disconnect()


def test_failing_callback_does_not_break_others(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    seen: list[Any] = []

    def bad(_msg: Any) -> None:
        raise RuntimeError("boom")

    rt.subscribe("ch_5", app_id="app_1", event_type="agent.message", callback=bad)
    rt.subscribe(
        "ch_5",
        app_id="app_1",
        event_type="agent.message",
        callback=seen.append,
    )
    msg = MagicMock()
    msg.topic = "axonpush/org_1/+/app_1/ch_5/agent_message/+"
    # Use a concrete topic so both subscribers' filters match.
    msg.topic = "axonpush/org_1/default/app_1/ch_5/agent_message/_"
    msg.payload = json.dumps({"x": 1}).encode("utf-8")
    rt._on_message(rt._mqtt, None, msg)
    assert seen == [{"x": 1}]
    rt.disconnect()


def test_callback_isolation_per_topic_filter(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    a: list[Any] = []
    b: list[Any] = []
    rt.subscribe("ch_5", app_id="app_1", event_type="agent.message", callback=a.append)
    rt.subscribe("ch_6", app_id="app_1", event_type="agent.message", callback=b.append)
    msg = MagicMock()
    msg.topic = "axonpush/org_1/default/app_1/ch_5/agent_message/_"
    msg.payload = json.dumps({"x": 1}).encode("utf-8")
    rt._on_message(rt._mqtt, None, msg)
    assert a == [{"x": 1}]
    assert b == []
    rt.disconnect()


def test_invalid_json_message_is_dropped(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    received: list[Any] = []
    rt.subscribe("ch_5", callback=received.append)
    msg = MagicMock()
    msg.topic = "axonpush/org_1/default/app_1/ch_5/custom/_"
    msg.payload = b"not-json"
    rt._on_message(rt._mqtt, None, msg)
    assert received == []
    rt.disconnect()


def test_refresh_only_scheduled_after_successful_connack(fake_facade, fake_paho) -> None:
    """Refresh-task race fix: refresh timer is created **only** after the
    broker confirms ``rc=0``. If CONNACK never arrives, ``connect()`` raises
    and no timer is left running with stale credentials."""
    _FakePaho.never_connack = True
    rt = RealtimeClient(fake_facade, keepalive=1)
    with pytest.raises(ConnectionError, match="CONNACK"):
        rt.connect()
    assert rt._refresh_timer is None


def test_refresh_not_scheduled_on_connack_failure(fake_facade, fake_paho) -> None:
    """``rc != 0`` means broker rejected the connection. The SDK must
    not schedule a refresh against credentials the broker refused."""
    _FakePaho.connack_rc = 5  # Not authorized
    rt = RealtimeClient(fake_facade, keepalive=1)
    with pytest.raises(ConnectionError):
        rt.connect()
    assert rt._refresh_timer is None


def test_disconnect_cancels_refresh_timer(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    assert rt._refresh_timer is not None
    timer = rt._refresh_timer
    rt.disconnect()
    assert rt._refresh_timer is None
    assert not timer.is_alive() or timer.finished.is_set()


def test_subscribe_only_calls_paho_when_connected(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    # Force-clear the connected flag so the call short-circuits.
    rt._connected.clear()
    rt.subscribe("ch_5", callback=lambda _m: None)
    # The subscription was recorded but not pushed to paho since not connected.
    assert "axonpush/org_1/+/+/ch_5/+/+" in rt._subscriptions
    assert ("axonpush/org_1/+/+/ch_5/+/+", 1) not in rt._mqtt.subscriptions
    rt.disconnect()


def test_unsubscribe_removes_handler(fake_facade, fake_paho) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()
    topic = rt.subscribe("ch_5", callback=lambda _m: None)
    rt.unsubscribe(topic)
    assert topic not in rt._subscriptions
    assert topic in rt._mqtt.unsubscriptions
    rt.disconnect()


def test_async_callback_on_sync_client_logs_warning(
    fake_facade, fake_paho, caplog: pytest.LogCaptureFixture
) -> None:
    rt = RealtimeClient(fake_facade)
    rt.connect()

    async def coro_cb(_msg: Any) -> None:
        return None

    rt.subscribe("ch_5", callback=coro_cb)
    msg = MagicMock()
    msg.topic = "axonpush/org_1/+/+/ch_5/+/+"
    # Concrete topic so the wildcard filter matches.
    msg.topic = "axonpush/org_1/default/app_1/ch_5/custom/_"
    msg.payload = json.dumps({"x": 1}).encode("utf-8")
    with caplog.at_level("WARNING", logger="axonpush.realtime"):
        rt._on_message(rt._mqtt, None, msg)
    assert any("async callback" in rec.message for rec in caplog.records)
    rt.disconnect()
