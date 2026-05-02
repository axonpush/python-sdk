"""Asynchronous MQTT-over-WSS realtime client.

Wraps `aiomqtt`. Mirrors :class:`axonpush.realtime.mqtt.RealtimeClient`
with ``asyncio.Lock`` synchronisation. Refresh runs as an
``asyncio.Task`` scheduled **after** the broker accepts the connection.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Union
from urllib.parse import urlparse

from axonpush.realtime.credentials import (
    IotCredentials,
    fetch_iot_credentials_async,
)
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic

if TYPE_CHECKING:
    from axonpush.client import AsyncAxonPush

logger = logging.getLogger("axonpush.realtime")

_DEFAULT_KEEPALIVE_S = 30
_REFRESH_LEAD_S = 60.0

EventCallback = Callable[[dict[str, Any]], Union[None, Awaitable[None]]]


def _import_aiomqtt() -> Any:
    try:
        import aiomqtt
    except ImportError as exc:
        raise ImportError(
            "Async MQTT support requires 'aiomqtt'. Install it with: pip install aiomqtt"
        ) from exc
    return aiomqtt


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


def _matches(topic_filter: str, topic: str) -> bool:
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


class AsyncRealtimeClient:
    """Async MQTT realtime client.

    Construct via :meth:`axonpush.client.AsyncAxonPush.connect_realtime`.
    Subscribers receive raw message dicts; callbacks may be sync or
    ``async def``. A failing callback is logged and skipped — it cannot
    crash the reader task.
    """

    def __init__(
        self,
        client: AsyncAxonPush,
        *,
        environment: str | None = None,
        keepalive: int = _DEFAULT_KEEPALIVE_S,
    ) -> None:
        self._client = client
        self._environment = environment
        self._keepalive = keepalive
        self._aiomqtt = _import_aiomqtt()
        self._mqtt: Any = None
        self._credentials: IotCredentials | None = None
        self._subscriptions: dict[str, tuple[int, EventCallback]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._refresh_task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()
        self._connected = asyncio.Event()
        self._lock = asyncio.Lock()

    @property
    def credentials(self) -> IotCredentials | None:
        return self._credentials

    async def aconnect(self) -> None:
        """Fetch credentials and open the MQTT-over-WSS connection.

        Raises:
            ConnectionError: Backend returned no credentials.
            aiomqtt.MqttError: Broker refused the connection.
        """
        creds = await fetch_iot_credentials_async(self._client)
        await self._activate(creds)

    async def connect(self) -> None:
        """Alias for :meth:`aconnect`."""
        await self.aconnect()

    async def _activate(self, creds: IotCredentials) -> None:
        host, port, path, scheme = _split_wss_url(creds.presigned_wss_url)
        mqtt = self._aiomqtt.Client(
            hostname=host,
            port=port,
            identifier=creds.client_id,
            transport="websockets",
            websocket_path=path,
            websocket_headers={"Sec-WebSocket-Protocol": "mqttv5.0"},
            tls_params=self._aiomqtt.TLSParameters() if scheme == "wss" else None,
            keepalive=self._keepalive,
            protocol=self._aiomqtt.ProtocolVersion.V5,
            username=creds.auth_token,
            password="" if creds.auth_token else None,
        )
        await mqtt.__aenter__()
        self._mqtt = mqtt
        self._credentials = creds
        self._connected.set()
        for topic, (qos, _cb) in self._subscriptions.items():
            await mqtt.subscribe(topic, qos=qos)
        self._reader_task = asyncio.create_task(self._reader())
        self._refresh_task = asyncio.create_task(self._refresher(creds))

    async def _reader(self) -> None:
        mqtt = self._mqtt
        if mqtt is None:
            return
        try:
            async for message in mqtt.messages:
                await self._dispatch(message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 — log and exit cleanly
            logger.warning("MQTT reader exited: %s", exc)

    async def _dispatch(self, message: Any) -> None:
        raw = getattr(message, "payload", b"")
        try:
            decoded = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            payload = json.loads(decoded)
        except (ValueError, UnicodeDecodeError) as exc:
            logger.debug("dropping non-JSON MQTT message: %s", exc)
            return
        topic = str(getattr(message, "topic", ""))
        async with self._lock:
            handlers = list(self._subscriptions.items())
        for topic_filter, (_qos, cb) in handlers:
            if not _matches(topic_filter, topic):
                continue
            try:
                result = cb(payload)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # noqa: BLE001 — never kill the reader
                logger.warning("realtime callback raised: %s", exc)

    async def _refresher(self, creds: IotCredentials) -> None:
        delay = max(creds.expires_in() - _REFRESH_LEAD_S, 1.0)
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        if self._stopped.is_set():
            return
        try:
            new_creds = await fetch_iot_credentials_async(self._client)
        except Exception as exc:  # noqa: BLE001 — log and bail; caller can reconnect
            logger.warning("IoT credential refresh failed: %s", exc)
            return
        async with self._lock:
            await self._tear_down_mqtt()
            try:
                await self._activate(new_creds)
            except Exception as exc:  # noqa: BLE001
                logger.warning("MQTT reconnect after credential refresh failed: %s", exc)

    async def _tear_down_mqtt(self) -> None:
        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
        self._reader_task = None
        if self._refresh_task is not None and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except (asyncio.CancelledError, Exception):
                pass
        self._refresh_task = None
        if self._mqtt is not None:
            try:
                await self._mqtt.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
        self._mqtt = None
        self._connected.clear()

    async def subscribe(
        self,
        channel_id: str,
        *,
        app_id: str | None = None,
        event_type: str | None = None,
        agent_id: str | None = None,
        callback: EventCallback,
        qos: int = 1,
    ) -> str:
        """Subscribe to events. See :meth:`RealtimeClient.subscribe`."""
        if self._credentials is None:
            raise RuntimeError("AsyncRealtimeClient.subscribe() called before connect()")
        topic = build_subscribe_topic(
            self._credentials.topic_prefix,
            app_id=app_id,
            channel_id=channel_id,
            event_type=event_type,
            agent_id=agent_id,
            env_slug=self._environment,
        )
        async with self._lock:
            self._subscriptions[topic] = (qos, callback)
        if self._mqtt is not None:
            await self._mqtt.subscribe(topic, qos=qos)
        return topic

    async def unsubscribe(self, topic: str) -> None:
        """Cancel a subscription."""
        async with self._lock:
            self._subscriptions.pop(topic, None)
        if self._mqtt is not None:
            await self._mqtt.unsubscribe(topic)

    async def publish(
        self,
        channel_id: str,
        *,
        app_id: str,
        event_type: str,
        agent_id: str | None = None,
        payload: dict[str, Any],
        qos: int = 1,
    ) -> None:
        """Publish a payload. See :meth:`RealtimeClient.publish`."""
        if self._mqtt is None or self._credentials is None:
            raise RuntimeError("AsyncRealtimeClient.publish() called before connect()")
        topic = build_publish_topic(
            self._credentials.topic_prefix,
            app_id=app_id,
            channel_id=channel_id,
            event_type=event_type,
            agent_id=agent_id,
            env_slug=self._environment,
            default_env_slug=self._credentials.env_slug,
        )
        await self._mqtt.publish(topic, payload=json.dumps(payload).encode("utf-8"), qos=qos)

    async def adisconnect(self) -> None:
        """Close the MQTT connection."""
        self._stopped.set()
        await self._tear_down_mqtt()

    async def disconnect(self) -> None:
        """Alias for :meth:`adisconnect`."""
        await self.adisconnect()
