"""MQTT transport tests — paho is fully mocked so no broker is needed."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from axonpush import AsyncAxonPush, AxonPush, EventType
from axonpush.models.events import Event
from axonpush.realtime.mqtt import RealtimeClient
from axonpush.realtime.mqtt_async import AsyncRealtimeClient

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _credential_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "endpoint": "abc-ats.iot.us-east-1.amazonaws.com",
            "presignedWssUrl": (
                "wss://abc-ats.iot.us-east-1.amazonaws.com/mqtt?X-Amz=token"
            ),
            "expiresAt": (
                datetime.now(timezone.utc) + timedelta(hours=1)
            ).isoformat(),
        },
    )


class _FakePahoClient:
    """Minimal stand-in for paho.mqtt.client.Client.

    Captures every call the SDK makes so we can assert on it. Fires
    ``on_connect`` synchronously when ``loop_start`` is called so the
    SDK's ``self._connected.wait()`` returns immediately.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.transport = kwargs.get("transport")
        self.connect_args: tuple = ()
        self.ws_options: dict = {}
        self.tls_set_called = False
        self.subscriptions: list[tuple[str, int]] = []
        self.unsubscriptions: list[str] = []
        self.published: list[tuple[str, bytes, int]] = []
        self.on_connect = lambda *a, **k: None
        self.on_disconnect = lambda *a, **k: None
        self.on_message = lambda *a, **k: None
        self.disconnected = False

    def ws_set_options(self, **kwargs: Any) -> None:
        self.ws_options = kwargs

    def tls_set(self, *args: Any, **kwargs: Any) -> None:
        self.tls_set_called = True

    def connect_async(self, host: str, port: int, keepalive: int = 30) -> None:
        self.connect_args = (host, port, keepalive)

    def loop_start(self) -> None:
        # Fire synthetic CONNACK so SDK can proceed.
        self.on_connect(self, None, {}, 0)

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


@pytest.fixture()
def fake_paho(monkeypatch):
    """Replace paho.mqtt.client.Client with a fake. Returns the fake instance
    on construction."""
    fake_module = MagicMock()
    fake_module.Client = _FakePahoClient
    fake_module.MQTTv311 = 4
    monkeypatch.setattr(
        "axonpush.realtime.mqtt._import_paho", lambda: fake_module
    )
    return fake_module


def test_connect_fetches_credentials_and_starts_loop(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        assert isinstance(rt._client, _FakePahoClient)
        assert rt._client.connect_args[0] == "abc-ats.iot.us-east-1.amazonaws.com"
        assert rt._client.connect_args[1] == 443
        assert rt._client.ws_options.get("path", "").startswith("/mqtt")
        assert rt._client.tls_set_called
        rt.disconnect()


def test_subscribe_builds_topic_and_calls_paho(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        rt.subscribe(
            "ch_5", event_type=EventType.AGENT_ERROR, agent_id="bot", environment="prod"
        )
        assert (
            "axonpush/org_1/prod/app_1/ch_5/agent_error/bot",
            1,
        ) in rt._client.subscriptions
        rt.disconnect()


def test_subscribe_without_env_uses_plus_wildcard(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        rt.subscribe("ch_5", event_type=EventType.AGENT_ERROR, agent_id="bot")
        assert (
            "axonpush/org_1/+/app_1/ch_5/agent_error/bot",
            1,
        ) in rt._client.subscriptions
        rt.disconnect()


def test_subscribe_without_filters_uses_wildcards(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        rt.subscribe("ch_5")
        assert ("axonpush/org_1/+/app_1/ch_5/+/+", 1) in rt._client.subscriptions
        rt.disconnect()


def test_publish_serialises_event_body(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        rt.publish(
            "ch_5",
            "tick",
            {"n": 1},
            event_type=EventType.AGENT_MESSAGE,
            agent_id="bot",
            environment="prod",
        )
        topic, body, qos = rt._client.published[-1]
        assert topic == "axonpush/org_1/prod/app_1/ch_5/agent_message/bot"
        assert qos == 1
        decoded = json.loads(body.decode("utf-8"))
        assert decoded["identifier"] == "tick"
        assert decoded["payload"] == {"n": 1}
        assert decoded["channelId"] == "ch_5"
        assert decoded["eventType"] == "agent.message"
        assert decoded["agentId"] == "bot"
        rt.disconnect()


def test_on_event_callback_receives_parsed_event(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    received: list[Event] = []
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()
        rt.on_event(received.append)
        message = MagicMock()
        message.payload = json.dumps(
            {
                "id": 1,
                "identifier": "tick",
                "payload": {"n": 1},
                "eventType": "agent.message",
            }
        ).encode("utf-8")
        rt._on_message(rt._client, None, message)
        assert len(received) == 1
        assert received[0].identifier == "tick"
        assert received[0].event_type == EventType.AGENT_MESSAGE
        rt.disconnect()


def test_publish_before_connect_raises(mock_router, fake_paho):
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        with pytest.raises(RuntimeError, match="connect"):
            rt.publish("ch_5", "x", {})


def test_connect_raises_when_credentials_unavailable(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(side_effect=httpx.ConnectError("no"))
    with AxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL, fail_open=True
    ) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        with pytest.raises(ConnectionError):
            rt.connect()


def test_callback_exception_is_swallowed(mock_router, fake_paho):
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport, org_id="org_1", app_id="app_1")
        rt.connect()

        def bad_cb(_evt: Event) -> None:
            raise RuntimeError("boom")

        seen: list[Event] = []
        rt.on_event(bad_cb)
        rt.on_event(seen.append)
        message = MagicMock()
        message.payload = json.dumps(
            {"id": 1, "identifier": "x", "payload": {}, "eventType": "custom"}
        ).encode("utf-8")
        rt._on_message(rt._client, None, message)
        assert len(seen) == 1
        rt.disconnect()


async def test_async_construction_imports_aiomqtt(monkeypatch):
    """If aiomqtt is missing, ``AsyncRealtimeClient.__init__`` raises
    ImportError up front. The error message must be actionable."""
    monkeypatch.setattr(
        "axonpush.realtime.mqtt_async._import_aiomqtt",
        lambda: (_ for _ in ()).throw(ImportError("aiomqtt missing")),
    )
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as c:
        with pytest.raises(ImportError, match="aiomqtt"):
            AsyncRealtimeClient(c._transport, org_id="org_1", app_id="app_1")


def test_connect_without_org_uses_plus(mock_router, fake_paho):
    """If org_id is omitted, the topic uses '+' so the broker fans out
    everything the IAM policy allows."""
    mock_router.get("/auth/iot-credentials").mock(return_value=_credential_response())
    with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
        rt = RealtimeClient(c._transport)
        rt.connect()
        rt.subscribe("ch_5")
        topics = [t for t, _ in rt._client.subscriptions]
        # tenant_id passed at client level becomes the org_id by default in
        # client.connect_realtime, but here we instantiate RealtimeClient
        # directly with no org_id, so it falls back to the '+' wildcard.
        assert any("axonpush/+/+/+/ch_5/+/+" == t for t in topics)
        rt.disconnect()
