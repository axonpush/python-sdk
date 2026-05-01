from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from axonpush._http import AsyncTransport
from axonpush.models.events import Event, EventType
from axonpush.realtime.credentials import IotCredentials, fetch_credentials_async
from axonpush.realtime.topics import build_publish_topic, build_subscribe_topic

logger = logging.getLogger("axonpush.mqtt")

_REFRESH_LEAD_S = 60.0
_DEFAULT_KEEPALIVE_S = 30


def _import_aiomqtt() -> Any:
    try:
        import aiomqtt
    except ImportError as exc:
        raise ImportError(
            "Async MQTT support requires 'aiomqtt'. Install it with: pip install aiomqtt"
        ) from exc
    return aiomqtt


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
    return (
        str(org_id) if org_id else "+",
        str(app_id) if app_id else "+",
        str(channel_id),
        event_type,
        agent_id,
    )


EventCallback = Callable[[Event], Union[None, Awaitable[None]]]


class AsyncRealtimeClient:
    """Asynchronous MQTT-over-WSS realtime client.

    Public surface preserved from the previous Socket.IO async version.
    Requires ``aiomqtt`` (a core dep — installed automatically with axonpush).
    """

    def __init__(
        self,
        transport: AsyncTransport,
        *,
        org_id: Optional[str] = None,
        app_id: Optional[str] = None,
        environment: Optional[str] = None,
        iot_endpoint: Optional[str] = None,
        keepalive: int = _DEFAULT_KEEPALIVE_S,
    ) -> None:
        self._transport = transport
        self._org_id = org_id
        self._app_id = app_id
        self._environment = environment
        self._iot_endpoint = iot_endpoint
        self._keepalive = keepalive
        self._aiomqtt = _import_aiomqtt()
        self._client: Any = None
        self._event_callbacks: List[EventCallback] = []
        self._subscriptions: List[Tuple[str, int]] = []
        self._credentials: Optional[IotCredentials] = None
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._refresh_task: Optional[asyncio.Task[None]] = None
        self._stopped = asyncio.Event()
        self._connected = asyncio.Event()
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        creds = await fetch_credentials_async(
            self._transport, iot_endpoint=self._iot_endpoint
        )
        if creds is None:
            raise ConnectionError(
                "Failed to fetch IoT credentials from /auth/iot-credentials"
            )
        await self._activate(creds)

    async def _activate(self, creds: IotCredentials) -> None:
        host, port, path, scheme = _split_wss_url(creds.presigned_wss_url)
        client = self._aiomqtt.Client(
            hostname=host,
            port=port,
            transport="websockets",
            websocket_path=path,
            tls_params=self._aiomqtt.TLSParameters() if scheme == "wss" else None,
            keepalive=self._keepalive,
        )
        await client.__aenter__()
        self._client = client
        self._credentials = creds
        self._connected.set()
        for topic, qos in self._subscriptions:
            await client.subscribe(topic, qos=qos)
        self._reader_task = asyncio.create_task(self._reader())
        self._refresh_task = asyncio.create_task(self._refresher(creds))

    async def _reader(self) -> None:
        client = self._client
        if client is None:
            return
        try:
            async for message in client.messages:
                await self._dispatch(message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("MQTT reader exited: %s", exc)

    async def _dispatch(self, message: Any) -> None:
        raw = getattr(message, "payload", b"")
        try:
            payload = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else str(raw))
        except (ValueError, UnicodeDecodeError):
            return
        try:
            event = Event.model_validate(payload)
        except Exception:
            return
        for cb in list(self._event_callbacks):
            try:
                result = cb(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                logger.warning("event callback raised: %s", exc)

    async def _refresher(self, creds: IotCredentials) -> None:
        delay = max(creds.expires_in() - _REFRESH_LEAD_S, 1.0)
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return
        if self._stopped.is_set():
            return
        try:
            new_creds = await fetch_credentials_async(
                self._transport, iot_endpoint=self._iot_endpoint
            )
        except Exception as exc:
            logger.warning("IoT credential refresh failed: %s", exc)
            return
        if new_creds is None:
            return
        async with self._lock:
            await self._tear_down_client()
            await self._activate(new_creds)

    async def _tear_down_client(self) -> None:
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
        if self._client is not None:
            try:
                await self._client.__aexit__(None, None, None)
            except Exception:
                pass
        self._client = None
        self._connected.clear()

    def on_event(self, callback: EventCallback) -> None:
        self._event_callbacks.append(callback)

    async def subscribe(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str]] = None,
        agent_id: Optional[str] = None,
        environment: Optional[str] = None,
        qos: int = 1,
    ) -> None:
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        env = environment if environment is not None else self._environment
        topic = build_subscribe_topic(
            org, app, ch, event_type=et, agent_id=ag, environment=env
        )
        self._subscriptions.append((topic, qos))
        if self._client is not None:
            await self._client.subscribe(topic, qos=qos)

    async def unsubscribe(
        self,
        channel_id: Union[int, str],
        *,
        event_type: Optional[Union[EventType, str]] = None,
        agent_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> None:
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        env = environment if environment is not None else self._environment
        topic = build_subscribe_topic(
            org, app, ch, event_type=et, agent_id=ag, environment=env
        )
        self._subscriptions = [s for s in self._subscriptions if s[0] != topic]
        if self._client is not None:
            await self._client.unsubscribe(topic)

    async def publish(
        self,
        channel_id: Union[int, str],
        identifier: str,
        payload: Dict[str, Any],
        *,
        event_type: Union[EventType, str] = EventType.CUSTOM,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        environment: Optional[str] = None,
        qos: int = 1,
    ) -> None:
        if self._client is None:
            raise RuntimeError("AsyncRealtimeClient.publish() called before connect()")
        org, app, ch, et, ag = _coerce_filter(
            self._org_id, self._app_id, channel_id, event_type, agent_id
        )
        env = environment if environment is not None else self._environment
        topic = build_publish_topic(
            org, app, ch,
            event_type=et or EventType.CUSTOM,
            agent_id=ag,
            environment=env,
        )
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
        await self._client.publish(topic, payload=json.dumps(body).encode("utf-8"), qos=qos)

    async def wait(self) -> None:
        await self._stopped.wait()

    async def disconnect(self) -> None:
        self._stopped.set()
        await self._tear_down_client()


AsyncWebSocketClient = AsyncRealtimeClient
