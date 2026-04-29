from __future__ import annotations

import warnings
from contextlib import contextmanager
from typing import Any, Iterator, Optional, Union

from axonpush._http import AsyncTransport, SyncTransport, _is_fail_open
from axonpush.models.channels import Channel, CreateChannelParams
from axonpush.models.events import Event, EventType


class _MqttSubscriptionShim:
    """Backward-compat wrapper that adapts the MQTT realtime client to the
    SSE iterator protocol used in v0.0.x. Removed in v0.2.0.
    """

    def __init__(
        self,
        client_factory: Any,
        channel_id: Union[int, str],
        *,
        agent_id: Optional[str],
        event_type: Optional[Union[EventType, str]],
    ) -> None:
        self._factory = client_factory
        self._channel_id = channel_id
        self._agent_id = agent_id
        self._event_type = event_type
        self._buffer: "list[Event]" = []
        self._cv: Any = None
        self._client: Any = None

    def __enter__(self) -> "_MqttSubscriptionShim":
        import threading as _threading

        self._cv = _threading.Condition()
        self._client = self._factory()
        if self._client is None:
            raise ConnectionError("Failed to open MQTT subscription via SSE shim")

        def _on_event(evt: Event) -> None:
            with self._cv:
                self._buffer.append(evt)
                self._cv.notify_all()

        self._client.on_event(_on_event)
        self._client.subscribe(
            self._channel_id, event_type=self._event_type, agent_id=self._agent_id
        )
        return self

    def __exit__(self, *args: Any) -> None:
        if self._client is not None:
            self._client.disconnect()
            self._client = None

    def __iter__(self) -> Iterator[Event]:
        if self._cv is None:
            raise RuntimeError("subscription must be used as a context manager")
        while True:
            with self._cv:
                while not self._buffer:
                    self._cv.wait()
                yield self._buffer.pop(0)


def _warn_sse_deprecated() -> None:
    warnings.warn(
        "channels.subscribe_sse is deprecated; switch to client.connect_realtime() "
        "(MQTT-over-WSS). The shim will be removed in v0.2.0.",
        DeprecationWarning,
        stacklevel=3,
    )


class ChannelsResource:
    """Synchronous resource for channel CRUD."""

    def __init__(self, transport: SyncTransport, *, owner: Any = None) -> None:
        self._transport = transport
        self._owner = owner

    def _attach_owner(self, owner: Any) -> None:
        self._owner = owner

    def create(self, name: str, app_id: Union[int, str]) -> Optional[Channel]:
        body = CreateChannelParams(name=name, app_id=app_id)
        data = self._transport.request(
            "POST", "/channel", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def get(self, channel_id: Union[int, str]) -> Optional[Channel]:
        data = self._transport.request("GET", f"/channel/{channel_id}")
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def update(self, channel_id: Union[int, str], **fields: Any) -> Optional[Channel]:
        data = self._transport.request("PUT", f"/channel/{channel_id}", json=fields)
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    def delete(self, channel_id: Union[int, str]) -> None:
        self._transport.request("DELETE", f"/channel/{channel_id}")

    @contextmanager
    def subscribe_sse(
        self,
        channel_id: Union[int, str],
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,  # noqa: ARG002 — kept for backwards compat
    ) -> Iterator["_MqttSubscriptionShim"]:
        _warn_sse_deprecated()
        owner = self._owner
        if owner is None:
            raise RuntimeError(
                "subscribe_sse requires the resource to be attached to an AxonPush client"
            )
        shim = _MqttSubscriptionShim(
            client_factory=lambda: owner.connect_realtime(),
            channel_id=channel_id,
            agent_id=agent_id,
            event_type=event_type,
        )
        with shim as sub:
            yield sub

    @contextmanager
    def subscribe_event_sse(
        self,
        channel_id: Union[int, str],
        event_identifier: str,  # noqa: ARG002 — server-side identifier filter not supported on MQTT
        *,
        agent_id: Optional[str] = None,
        event_type: Optional[Union[EventType, str]] = None,
        trace_id: Optional[str] = None,  # noqa: ARG002
    ) -> Iterator["_MqttSubscriptionShim"]:
        _warn_sse_deprecated()
        owner = self._owner
        if owner is None:
            raise RuntimeError(
                "subscribe_event_sse requires the resource to be attached to an AxonPush client"
            )
        shim = _MqttSubscriptionShim(
            client_factory=lambda: owner.connect_realtime(),
            channel_id=channel_id,
            agent_id=agent_id,
            event_type=event_type,
        )
        with shim as sub:
            yield sub


class AsyncChannelsResource:
    """Asynchronous resource for channel CRUD."""

    def __init__(self, transport: AsyncTransport, *, owner: Any = None) -> None:
        self._transport = transport
        self._owner = owner

    def _attach_owner(self, owner: Any) -> None:
        self._owner = owner

    async def create(self, name: str, app_id: Union[int, str]) -> Optional[Channel]:
        body = CreateChannelParams(name=name, app_id=app_id)
        data = await self._transport.request(
            "POST", "/channel", json=body.model_dump(by_alias=True, exclude_none=True)
        )
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def get(self, channel_id: Union[int, str]) -> Optional[Channel]:
        data = await self._transport.request("GET", f"/channel/{channel_id}")
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def update(self, channel_id: Union[int, str], **fields: Any) -> Optional[Channel]:
        data = await self._transport.request("PUT", f"/channel/{channel_id}", json=fields)
        if _is_fail_open(data):
            return None
        return Channel.model_validate(data)

    async def delete(self, channel_id: Union[int, str]) -> None:
        await self._transport.request("DELETE", f"/channel/{channel_id}")
