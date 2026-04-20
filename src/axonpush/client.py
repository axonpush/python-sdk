from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Iterator, Optional

from axonpush._auth import AuthConfig
from axonpush._http import AsyncTransport, SyncTransport
from axonpush.realtime.websocket import AsyncWebSocketClient, WebSocketClient
from axonpush.resources.apps import AppsResource, AsyncAppsResource
from axonpush.resources.channels import AsyncChannelsResource, ChannelsResource
from axonpush.resources.events import AsyncEventsResource, EventsResource
from axonpush.resources.traces import AsyncTracesResource, TracesResource
from axonpush.resources.webhooks import AsyncWebhooksResource, WebhooksResource

logger = logging.getLogger("axonpush")

_ENV_VAR_PRECEDENCE = (
    "AXONPUSH_ENVIRONMENT",
    "SENTRY_ENVIRONMENT",
    "APP_ENV",
    "ENV",
)


def _detect_environment() -> Optional[str]:
    for name in _ENV_VAR_PRECEDENCE:
        val = os.getenv(name)
        if val:
            return val
    return None


class AxonPush:
    """Synchronous AxonPush client. Thread-safe.

    Usage::

        with AxonPush(api_key="ak_...", tenant_id="1", environment="production") as client:
            event = client.events.publish(
                "web_search", {"query": "AI agents"}, channel_id=1,
                agent_id="researcher", event_type="agent.tool_call.start",
            )
    """

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        *,
        base_url: str = "https://api.axonpush.xyz",
        timeout: float = 30.0,
        fail_open: bool = True,
        environment: Optional[str] = None,
    ) -> None:
        resolved_env = environment if environment is not None else _detect_environment()
        if resolved_env:
            logger.debug(
                "AxonPush environment=%s (resolved from %s)",
                resolved_env,
                "parameter" if environment else "env var",
            )
        self._auth = AuthConfig(api_key, tenant_id, base_url, environment=resolved_env)
        self._fail_open = fail_open
        self._transport = SyncTransport(self._auth, timeout, fail_open=fail_open)

        self.events = EventsResource(self._transport, environment=resolved_env)
        self.channels = ChannelsResource(self._transport)
        self.apps = AppsResource(self._transport)
        self.webhooks = WebhooksResource(self._transport)
        self.traces = TracesResource(self._transport)

    @contextmanager
    def environment(self, env: str) -> Iterator[None]:
        """Temporarily override the default environment for calls made inside the block."""
        previous = self.events._environment
        self.events._environment = env
        try:
            yield
        finally:
            self.events._environment = previous

    def connect_websocket(self) -> Optional[WebSocketClient]:
        ws = WebSocketClient(self._auth)
        try:
            ws.connect()
        except Exception as exc:
            if self._fail_open:
                logger.warning(
                    "AxonPush WebSocket connection failed: %s. "
                    "The error was suppressed (fail_open=True).",
                    exc,
                )
                return None
            raise
        return ws

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "AxonPush":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncAxonPush:
    """Asynchronous AxonPush client. Task-safe."""

    def __init__(
        self,
        api_key: str,
        tenant_id: str,
        *,
        base_url: str = "https://api.axonpush.xyz",
        timeout: float = 30.0,
        fail_open: bool = True,
        environment: Optional[str] = None,
    ) -> None:
        resolved_env = environment if environment is not None else _detect_environment()
        if resolved_env:
            logger.debug(
                "AxonPush environment=%s (resolved from %s)",
                resolved_env,
                "parameter" if environment else "env var",
            )
        self._auth = AuthConfig(api_key, tenant_id, base_url, environment=resolved_env)
        self._fail_open = fail_open
        self._transport = AsyncTransport(self._auth, timeout, fail_open=fail_open)

        self.events = AsyncEventsResource(self._transport, environment=resolved_env)
        self.channels = AsyncChannelsResource(self._transport)
        self.apps = AsyncAppsResource(self._transport)
        self.webhooks = AsyncWebhooksResource(self._transport)
        self.traces = AsyncTracesResource(self._transport)

    @contextmanager
    def environment(self, env: str) -> Iterator[None]:
        previous = self.events._environment
        self.events._environment = env
        try:
            yield
        finally:
            self.events._environment = previous

    async def connect_websocket(self) -> Optional[AsyncWebSocketClient]:
        ws = AsyncWebSocketClient(self._auth)
        try:
            await ws.connect()
        except Exception as exc:
            if self._fail_open:
                logger.warning(
                    "AxonPush WebSocket connection failed: %s. "
                    "The error was suppressed (fail_open=True).",
                    exc,
                )
                return None
            raise
        return ws

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> "AsyncAxonPush":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
