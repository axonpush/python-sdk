from __future__ import annotations

import json
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from axonpush._http import SyncTransport
from axonpush.models.events import Event, EventType
from axonpush.realtime.credentials import IotCredentials, fetch_credentials_sync
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic

logger = logging.getLogger("axonpush.mqtt")

_DEFAULT_KEEPALIVE_S = 30
_REFRESH_LEAD_S = 60.0


def _import_paho() -> Any:
    try:
        import paho.mqtt.client as paho_client
    except ImportError as exc:
        raise ImportError(
            "MQTT support requires 'paho-mqtt'. Install it with: pip install paho-mqtt"
        ) from exc
    return paho_client


def _split_wss_url(url: str) -> Tuple[str, int, str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("wss", "ws"):
        raise ValueError(f"presigned IoT URL must be wss:// (got {parsed.scheme!r})")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    path = parsed.path or "/mqtt"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return host, port, path, parsed.scheme


def _coerce_filter(
    org_id: Optional[str],
    app_id: Optional[str],
    channel_id: Union[int, str],
    event_type: Optional[Union[str, EventType]],
    agent_id: Optional[str],
) -> Tuple[str, str, str, Optional[Union[str, EventType]], Optional[str]]:
    if not org_id:
        org_id = "+"
    if not app_id:
        app_id = "+"
    return str(org_id), str(app_id), str(channel_id), event_type, agent_id


class RealtimeClient:
    """Synchronous MQTT-over-WSS realtime client.

    Public surface preserved from the previous Socket.IO version:
    ``connect()``, ``on_event(callback)``, ``subscribe(channel, ...)``,
    ``publish(...)``, ``wait()``, ``disconnect()``.

    Requires ``paho-mqtt`` (a core dep — installed automatically with axonpush).
    """

    def __init__(
        self,
        transport: SyncTransport,
        *,
        org_id: Optional[str] = None,
        app_id: Optional[str] = None,
        iot_endpoint: Optional[str] = None,
        keepalive: int = _DEFAULT_KEEPALIVE_S,
    ) -> None:
        self._transport = transport
        self._org_id = org_id
        self._app_id = app_id
        self._iot_endpoint = iot_endpoint
        self._keepalive = keepalive
        self._paho = _import_paho()
        self._client: Any = None
        self._event_callbacks: List[Callable[[Event], Any]] = []
        self._subscriptions: List[Tuple[str, int]] = []
        self._credentials: Optional[IotCredentials] = None
        self._connected = threading.Event()
        self._closed = threading.Event()
        self._refresh_timer: Optional[threading.Timer] = None
        self._lock = threading.RLock()

    def connect(self) -> None:
        creds = fetch_credentials_sync(self._transport, iot_endpoint=self._iot_endpoint)
        if creds is None:
            raise ConnectionError(
                "Failed to fetch IoT credentials from /auth/iot-credentials"
            )
        self._credentials = creds
        self._build_client(creds)
        self._client.loop_start()
        if not self._connected.wait(timeout=self._keepalive):
            raise ConnectionError("MQTT broker did not signal CONNACK in time")
        self._schedule_refresh(creds)

    def _build_client(self, creds: IotCredentials) -> None:
        host, port, path, scheme = _split_wss_url(creds.presigned_wss_url)
        client = self._paho.Client(transport="websockets", protocol=self._paho.MQTTv311)
        client.ws_set_options(path=path)
        if scheme == "wss":
            client.tls_set()
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        self._client = client
        client.connect_async(host, port, keepalive=self._keepalive)

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: int, *_: Any) -> None:
        if rc != 0:
            logger.warning("MQTT CONNACK rc=%s", rc)
            return
        self._connected.set()
        with self._lock:
            for topic, qos in self._subscriptions:
                client.subscribe(topic, qos=qos)

    def _on_disconnect(self, client: Any, userdata: Any, rc: int, *_: Any) -> None:
        self._connected.clear()
        if rc != 0:
            logger.warning("MQTT disconnect rc=%s", rc)

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return
        try:
            event = Event.model_validate(payload)
        except Exception:
            return
        for cb in list(self._event_callbacks):
            try:
                cb(event)
            except Exception as exc:
                logger.warning("event callback raised: %s", exc)

    def _schedule_refresh(self, creds: IotCredentials) -> None:
        delay = max(creds.expires_in() - _REFRESH_LEAD_S, 1.0)
        timer = threading.Timer(delay, self._refresh_credentials)
        timer.daemon = True
        timer.start()
        self._refresh_timer = timer

    def _refresh_credentials(self) -> None:
        if self._closed.is_set():
            return
        try:
            new_creds = fetch_credentials_sync(
                self._transport, iot_endpoint=self._iot_endpoint
            )
        except Exception as exc:
            logger.warning("IoT credential refresh failed: %s", exc)
            return
        if new_creds is None:
            return
        try:
            self._client.disconnect()
            self._client.loop_stop()
        except Exception:
            pass
        self._credentials = new_creds
        self._connected.clear()
        self._build_client(new_creds)
        self._client.loop_start()
        if not self._connected.wait(timeout=self._keepalive):
            logger.warning("MQTT broker did not reconnect after credential refresh")
            return
        self._schedule_refresh(new_creds)

    def on_event(self, callback: Callable[[Event], Any]) -> None:
        self._event_callbacks.append(callback)

    def subscribe(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str]] = None,
        agent_id: Optional[str] = None,
        qos: int = 1,
    ) -> None:
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        topic = build_subscribe_topic(org, app, ch, event_type=et, agent_id=ag)
        with self._lock:
            self._subscriptions.append((topic, qos))
        if self._client is not None and self._connected.is_set():
            self._client.subscribe(topic, qos=qos)

    def unsubscribe(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str]] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        topic = build_subscribe_topic(org, app, ch, event_type=et, agent_id=ag)
        with self._lock:
            self._subscriptions = [s for s in self._subscriptions if s[0] != topic]
        if self._client is not None:
            self._client.unsubscribe(topic)

    def publish(
        self,
        channel_id: Union[int, str],
        identifier: str,
        payload: Dict[str, Any],
        *,
        event_type: Union[EventType, str] = EventType.CUSTOM,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        qos: int = 1,
    ) -> None:
        if self._client is None:
            raise RuntimeError("RealtimeClient.publish() called before connect()")
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        topic = build_publish_topic(org, app, ch, event_type=et or EventType.CUSTOM, agent_id=ag)
        body: Dict[str, Any] = {
            "identifier": identifier,
            "payload": payload,
            "channelId": channel_id,
            "eventType": (
                event_type.value if isinstance(event_type, EventType) else event_type
            ),
        }
        if agent_id is not None:
            body["agentId"] = agent_id
        if trace_id is not None:
            body["traceId"] = trace_id
        self._client.publish(topic, payload=json.dumps(body), qos=qos)

    def wait(self) -> None:
        self._closed.wait()

    def disconnect(self) -> None:
        self._closed.set()
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()
            self._refresh_timer = None
        if self._client is not None:
            try:
                self._client.disconnect()
                self._client.loop_stop()
            except Exception:
                pass


WebSocketClient = RealtimeClient
