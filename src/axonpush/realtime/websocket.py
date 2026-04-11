from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

from axonpush._auth import AuthConfig
from axonpush.models.events import Event, EventType


class WebSocketClient:
    """Synchronous Socket.IO client for the /events namespace.

    Requires the ``websocket`` extra: ``pip install axonpush[websocket]``

    Usage::

        ws = client.connect_websocket()
        ws.on_event(lambda e: print(e.agent_id, e.payload))
        ws.subscribe(channel_id=1, event_type=EventType.AGENT_ERROR)
        ws.wait()  # blocks until disconnect
    """

    def __init__(self, auth: AuthConfig) -> None:
        try:
            import socketio  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "WebSocket support requires the 'websocket' extra. "
                "Install it with: pip install axonpush[websocket]"
            ) from None

        self._auth = auth
        self._sio = socketio.Client()
        self._event_callbacks: List[Callable[[Event], Any]] = []
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        @self._sio.on("event", namespace="/events")  # type: ignore[untyped-decorator]
        def on_event(data: Dict[str, Any]) -> None:
            try:
                event = Event.model_validate(data)
            except Exception:
                return
            for cb in self._event_callbacks:
                cb(event)

    def connect(self) -> None:
        """Connect to the AxonPush WebSocket server."""
        self._sio.connect(
            self._auth.base_url,
            namespaces=["/events"],
            auth={"apiKey": self._auth.api_key},
        )

    def subscribe(
        self,
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        """Subscribe to a channel with optional filters."""
        data: Dict[str, Any] = {"channelId": channel_id}
        if agent_id is not None:
            data["agentId"] = agent_id
        if event_type is not None:
            data["eventType"] = str(
                event_type.value if isinstance(event_type, EventType) else event_type
            )
        if trace_id is not None:
            data["traceId"] = trace_id
        self._sio.emit("subscribe", data, namespace="/events")

    def unsubscribe(self, channel_id: int) -> None:
        """Unsubscribe from a channel."""
        self._sio.emit("unsubscribe", {"channelId": channel_id}, namespace="/events")

    def publish(
        self,
        channel_id: int,
        identifier: str,
        payload: Dict[str, Any],
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
    ) -> None:
        """Publish an event via WebSocket."""
        data: Dict[str, Any] = {
            "channelId": channel_id,
            "identifier": identifier,
            "payload": payload,
        }
        if agent_id is not None:
            data["agentId"] = agent_id
        if trace_id is not None:
            data["traceId"] = trace_id
        if event_type is not None:
            data["eventType"] = str(
                event_type.value if isinstance(event_type, EventType) else event_type
            )
        self._sio.emit("publish", data, namespace="/events")

    def on_event(self, callback: Callable[[Event], Any]) -> None:
        """Register a callback for incoming events."""
        self._event_callbacks.append(callback)

    def wait(self) -> None:
        """Block until the connection is closed."""
        self._sio.wait()

    def disconnect(self) -> None:
        """Disconnect from the server."""
        self._sio.disconnect()


class AsyncWebSocketClient:
    """Asynchronous Socket.IO client for the /events namespace.

    Requires the ``websocket`` extra: ``pip install axonpush[websocket]``
    """

    def __init__(self, auth: AuthConfig) -> None:
        try:
            import socketio
        except ImportError:
            raise ImportError(
                "WebSocket support requires the 'websocket' extra. "
                "Install it with: pip install axonpush[websocket]"
            ) from None

        self._auth = auth
        self._sio = socketio.AsyncClient()
        self._event_callbacks: List[Callable[[Event], Any]] = []
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        @self._sio.on("event", namespace="/events")  # type: ignore[untyped-decorator]
        async def on_event(data: Dict[str, Any]) -> None:
            try:
                event = Event.model_validate(data)
            except Exception:
                return
            for cb in self._event_callbacks:
                result = cb(event)
                if hasattr(result, "__await__"):
                    await result

    async def connect(self) -> None:
        await self._sio.connect(
            self._auth.base_url,
            namespaces=["/events"],
            auth={"apiKey": self._auth.api_key},
        )

    async def subscribe(
        self,
        channel_id: int,
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        data: Dict[str, Any] = {"channelId": channel_id}
        if agent_id is not None:
            data["agentId"] = agent_id
        if event_type is not None:
            data["eventType"] = str(
                event_type.value if isinstance(event_type, EventType) else event_type
            )
        if trace_id is not None:
            data["traceId"] = trace_id
        await self._sio.emit("subscribe", data, namespace="/events")

    async def unsubscribe(self, channel_id: int) -> None:
        await self._sio.emit("unsubscribe", {"channelId": channel_id}, namespace="/events")

    async def publish(
        self,
        channel_id: int,
        identifier: str,
        payload: Dict[str, Any],
        *,
        agent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
    ) -> None:
        data: Dict[str, Any] = {
            "channelId": channel_id,
            "identifier": identifier,
            "payload": payload,
        }
        if agent_id is not None:
            data["agentId"] = agent_id
        if trace_id is not None:
            data["traceId"] = trace_id
        if event_type is not None:
            data["eventType"] = str(
                event_type.value if isinstance(event_type, EventType) else event_type
            )
        await self._sio.emit("publish", data, namespace="/events")

    def on_event(self, callback: Callable[[Event], Any]) -> None:
        self._event_callbacks.append(callback)

    async def wait(self) -> None:
        await self._sio.wait()

    async def disconnect(self) -> None:
        await self._sio.disconnect()
