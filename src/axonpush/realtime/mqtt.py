"""Synchronous MQTT-over-WSS realtime client.

Wraps `paho-mqtt`. Public surface: :class:`RealtimeClient` only.
Credentials are fetched via the generated ``/auth/iot-credentials`` op
and refreshed before they expire — but the refresh task is scheduled
**only after** the broker confirms a successful CONNACK. If the initial
connection fails, no refresh fires and the caller is free to retry.
"""

from __future__ import annotations

import inspect
import json
import logging
import threading
from typing import TYPE_CHECKING, Any, Callable
from urllib.parse import urlparse

from axonpush.realtime.credentials import (
    IotCredentials,
    fetch_iot_credentials_sync,
)
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic

if TYPE_CHECKING:
    from axonpush.client import AxonPush

logger = logging.getLogger("axonpush.realtime")

_DEFAULT_KEEPALIVE_S = 30
_REFRESH_LEAD_S = 60.0

EventCallback = Callable[[dict[str, Any]], Any]


def _import_paho() -> Any:
    try:
        import paho.mqtt.client as paho_client
    except ImportError as exc:
        raise ImportError(
            "MQTT support requires 'paho-mqtt'. Install it with: pip install paho-mqtt"
        ) from exc
    return paho_client


def _split_wss_url(url: str) -> tuple[str, int, str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in ("wss", "ws"):
        raise ValueError(f"presigned IoT URL must be wss:// (got {parsed.scheme!r})")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    path = parsed.path or "/mqtt"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return host, port, path, parsed.scheme


class RealtimeClient:
    """Sync MQTT realtime client.

    Construct via :meth:`axonpush.client.AxonPush.connect_realtime` rather
    than directly so the facade can wire in fail-open behavior. Subscribers
    receive raw message dicts (the broker's JSON payload) on per-channel
    callbacks; both sync and ``async def`` callbacks are supported. A
    callback that raises is logged and skipped so it cannot kill the
    reader thread or starve other callbacks for the same message.
    """

    def __init__(
        self,
        client: AxonPush,
        *,
        environment: str | None = None,
        keepalive: int = _DEFAULT_KEEPALIVE_S,
    ) -> None:
        self._client = client
        self._environment = environment
        self._keepalive = keepalive
        self._paho = _import_paho()
        self._mqtt: Any = None
        self._credentials: IotCredentials | None = None
        self._subscriptions: dict[str, tuple[int, EventCallback]] = {}
        self._connected = threading.Event()
        self._closed = threading.Event()
        self._refresh_timer: threading.Timer | None = None
        self._lock = threading.RLock()

    @property
    def credentials(self) -> IotCredentials | None:
        return self._credentials

    def connect(self) -> None:
        """Fetch credentials and open the MQTT-over-WSS connection.

        Raises:
            ConnectionError: If the broker does not return CONNACK within
                ``keepalive`` seconds, or if credentials cannot be fetched.
        """
        creds = fetch_iot_credentials_sync(self._client)
        self._credentials = creds
        self._build_client(creds)
        self._mqtt.loop_start()
        if not self._connected.wait(timeout=self._keepalive):
            raise ConnectionError("MQTT broker did not signal CONNACK in time")
        self._schedule_refresh(creds)

    def _build_client(self, creds: IotCredentials) -> None:
        host, port, path, scheme = _split_wss_url(creds.presigned_wss_url)
        mqtt = self._paho.Client(
            client_id=creds.client_id,
            transport="websockets",
            protocol=self._paho.MQTTv5,
        )
        mqtt.ws_set_options(path=path, headers={"Sec-WebSocket-Protocol": "mqttv5.0"})
        if creds.auth_token:
            mqtt.username_pw_set(creds.auth_token, password="")
        if scheme == "wss":
            mqtt.tls_set()
        mqtt.on_connect = self._on_connect
        mqtt.on_disconnect = self._on_disconnect
        mqtt.on_message = self._on_message
        self._mqtt = mqtt
        mqtt.connect_async(host, port, keepalive=self._keepalive)

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: int, *_: Any) -> None:
        if rc != 0:
            logger.warning("MQTT CONNACK rc=%s — connection rejected", rc)
            return
        self._connected.set()
        with self._lock:
            for topic, (qos, _cb) in self._subscriptions.items():
                client.subscribe(topic, qos=qos)

    def _on_disconnect(self, client: Any, userdata: Any, rc: int, *_: Any) -> None:
        self._connected.clear()
        if rc != 0:
            logger.warning("MQTT disconnect rc=%s", rc)

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, AttributeError) as exc:
            logger.debug("dropping non-JSON MQTT message: %s", exc)
            return
        with self._lock:
            handlers = list(self._subscriptions.items())
        for topic_filter, (_qos, cb) in handlers:
            if not _matches(topic_filter, message.topic):
                continue
            try:
                result = cb(payload)
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    logger.warning(
                        "async callback registered on sync RealtimeClient — "
                        "use AsyncRealtimeClient instead; coroutine was discarded"
                    )
            except Exception as exc:
                logger.warning("realtime callback raised: %s", exc)

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
            new_creds = fetch_iot_credentials_sync(self._client)
        except Exception as exc:
            logger.warning("IoT credential refresh failed: %s", exc)
            return
        try:
            self._mqtt.disconnect()
            self._mqtt.loop_stop()
        except Exception:  # noqa: BLE001 — best-effort tear-down
            pass
        self._connected.clear()
        self._credentials = new_creds
        self._build_client(new_creds)
        self._mqtt.loop_start()
        if not self._connected.wait(timeout=self._keepalive):
            logger.warning(
                "MQTT broker did not reconnect after credential refresh; "
                "leaving refresh loop — caller should reconnect"
            )
            return
        self._schedule_refresh(new_creds)

    def subscribe(
        self,
        channel_id: str,
        *,
        app_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        callback: EventCallback,
        qos: int = 1,
    ) -> str:
        """Subscribe to events matching the given filter.

        Args:
            channel_id: Channel UUID. Required.
            app_id: Optional app filter. ``None`` matches any app.
            event_type: Optional event-type filter (string).
            agent_id: Optional agent filter.
            callback: Sync callable receiving the decoded JSON payload.
                Async callables registered here are rejected at dispatch
                time — use :class:`AsyncRealtimeClient` instead.
            qos: MQTT QoS — defaults to 1.

        Returns:
            The MQTT topic filter that was subscribed to. Pass this back
            to :meth:`unsubscribe`.
        """
        if self._credentials is None:
            raise RuntimeError("RealtimeClient.subscribe() called before connect()")
        topic = build_subscribe_topic(
            self._credentials.topic_prefix,
            app_id=app_id,
            channel_id=channel_id,
            event_type=event_type,
            agent_id=agent_id,
            env_slug=self._environment,
        )
        with self._lock:
            self._subscriptions[topic] = (qos, callback)
        if self._mqtt is not None and self._connected.is_set():
            self._mqtt.subscribe(topic, qos=qos)
        return topic

    def unsubscribe(self, topic: str) -> None:
        """Cancel a subscription previously returned by :meth:`subscribe`."""
        with self._lock:
            self._subscriptions.pop(topic, None)
        if self._mqtt is not None:
            self._mqtt.unsubscribe(topic)

    def publish(
        self,
        channel_id: str,
        *,
        app_id: str,
        event_type: str,
        agent_id: str | None = None,
        payload: dict[str, Any],
        qos: int = 1,
    ) -> None:
        """Publish a payload to a channel topic.

        Args:
            channel_id: Channel UUID.
            app_id: App UUID (required on publish).
            event_type: Event type string (e.g. ``"agent.message"``).
            agent_id: Optional agent UUID.
            payload: JSON-serialisable body.
            qos: MQTT QoS — defaults to 1.

        Raises:
            RuntimeError: If called before :meth:`connect`.
        """
        if self._mqtt is None or self._credentials is None:
            raise RuntimeError("RealtimeClient.publish() called before connect()")
        topic = build_publish_topic(
            self._credentials.topic_prefix,
            app_id=app_id,
            channel_id=channel_id,
            event_type=event_type,
            agent_id=agent_id,
            env_slug=self._environment,
            default_env_slug=self._credentials.env_slug,
        )
        self._mqtt.publish(topic, payload=json.dumps(payload), qos=qos)

    def disconnect(self) -> None:
        """Close the MQTT connection and cancel any pending refresh."""
        self._closed.set()
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()
            self._refresh_timer = None
        if self._mqtt is not None:
            try:
                self._mqtt.disconnect()
                self._mqtt.loop_stop()
            except Exception:  # noqa: BLE001 — best-effort tear-down
                pass


def _matches(topic_filter: str, topic: str) -> bool:
    """Match an MQTT topic filter against a concrete topic.

    Implements ``+`` (single-level) and ``#`` (multi-level) wildcards as
    defined by MQTT 3.1.1 §4.7.
    """
    f_parts = topic_filter.split("/")
    t_parts = topic.split("/")
    for i, fp in enumerate(f_parts):
        if fp == "#":
            return True
        if i >= len(t_parts):
            return False
        if fp == "+":
            continue
        if fp != t_parts[i]:
            return False
    return len(f_parts) == len(t_parts)
