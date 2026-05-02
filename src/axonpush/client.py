"""Public facade for the AxonPush SDK.

Provides :class:`AxonPush` (synchronous) and :class:`AsyncAxonPush`
(asynchronous) clients. Both expose lazily-loaded resource accessors and a
single ``_invoke`` chokepoint that all resource modules route through, so
retries, fail-open semantics and request-id propagation stay in one place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypeVar

from pydantic import HttpUrl, SecretStr

from axonpush._config import Settings
from axonpush._internal.transport import (
    build_async_client,
    build_sync_client,
    call_with_retries_async,
    call_with_retries_sync,
)
from axonpush.exceptions import APIConnectionError

if TYPE_CHECKING:
    from axonpush._internal.api.client import AuthenticatedClient

R = TypeVar("R")


def _build_settings(
    *,
    api_key: str | SecretStr | None,
    tenant_id: str | None,
    base_url: str | HttpUrl | None,
    environment: str | None,
    timeout: float | None,
    max_retries: int | None,
    fail_open: bool | None,
) -> Settings:
    base = Settings()
    overrides: dict[str, Any] = {}
    if api_key is not None:
        overrides["api_key"] = (
            api_key if isinstance(api_key, SecretStr) else SecretStr(api_key)
        )
    if tenant_id is not None:
        overrides["tenant_id"] = tenant_id
    if base_url is not None:
        overrides["base_url"] = (
            base_url if isinstance(base_url, HttpUrl) else HttpUrl(str(base_url))
        )
    if environment is not None:
        overrides["environment"] = environment
    if timeout is not None:
        overrides["timeout"] = timeout
    if max_retries is not None:
        overrides["max_retries"] = max_retries
    if fail_open is not None:
        overrides["fail_open"] = fail_open
    if not overrides:
        return base
    return base.model_copy(update=overrides)


class AxonPush:
    """Synchronous AxonPush client.

    Args:
        api_key: API key. Falls back to ``AXONPUSH_API_KEY``.
        tenant_id: Tenant id. Falls back to ``AXONPUSH_TENANT_ID``.
        base_url: Backend base URL. Falls back to ``AXONPUSH_BASE_URL``.
        environment: Logical environment label (sent as
            ``X-Axonpush-Environment``). Falls back to
            ``AXONPUSH_ENVIRONMENT``.
        timeout: Per-request timeout in seconds. Falls back to
            ``AXONPUSH_TIMEOUT``.
        max_retries: Number of retry attempts on retryable failures. Falls
            back to ``AXONPUSH_MAX_RETRIES``.
        fail_open: When true, suppress
            :class:`~axonpush.exceptions.APIConnectionError` and return
            ``None`` from :meth:`_invoke`. Falls back to
            ``AXONPUSH_FAIL_OPEN``.

    Example::

        with AxonPush(api_key="ak_...", tenant_id="org_...") as client:
            client.events.publish(...)
    """

    def __init__(
        self,
        *,
        api_key: str | SecretStr | None = None,
        tenant_id: str | None = None,
        base_url: str | HttpUrl | None = None,
        environment: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        fail_open: bool | None = None,
    ) -> None:
        self._settings = _build_settings(
            api_key=api_key,
            tenant_id=tenant_id,
            base_url=base_url,
            environment=environment,
            timeout=timeout,
            max_retries=max_retries,
            fail_open=fail_open,
        )
        self._client: AuthenticatedClient = build_sync_client(self._settings)
        self._closed = False

    @property
    def environment(self) -> str | None:
        """Return the configured environment label, or ``None`` if unset."""
        return self._settings.environment

    @property
    def fail_open(self) -> bool:
        """Whether the facade swallows :class:`APIConnectionError`."""
        return self._settings.fail_open

    @property
    def settings(self) -> Settings:
        """The frozen :class:`Settings` powering this client."""
        return self._settings

    @property
    def http(self) -> "AuthenticatedClient":
        """The underlying generated HTTP client (for resource modules)."""
        return self._client

    def _invoke(
        self,
        op: Any,
        *,
        _coerce: Callable[[Any], R] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call ``op.sync_detailed`` through the retry layer.

        Args:
            op: The generated operation module to invoke.
            _coerce: Optional transform applied to ``response.parsed``
                before returning.
            **kwargs: Keyword args forwarded to ``op.sync_detailed``.

        Returns:
            The parsed response (optionally coerced), or ``None`` when
            ``fail_open=True`` and the call raised
            :class:`APIConnectionError`.

        Raises:
            AxonPushError: When the call fails and ``fail_open`` is false
                (or the failure is not a connection error).
        """
        try:
            response = call_with_retries_sync(
                op,
                client=self._client,
                max_retries=self._settings.max_retries,
                **kwargs,
            )
        except APIConnectionError:
            if self._settings.fail_open:
                return None
            raise
        parsed = getattr(response, "parsed", response)
        if _coerce is not None and parsed is not None:
            return _coerce(parsed)
        return parsed

    def close(self) -> None:
        """Close the underlying HTTP client. Idempotent."""
        if self._closed:
            return
        self._client.get_httpx_client().close()
        self._closed = True

    def __enter__(self) -> "AxonPush":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _resource(self, module_name: str, class_name: str) -> Any:
        import importlib

        module = importlib.import_module(f"axonpush.resources.{module_name}")
        return getattr(module, class_name)(self)

    @property
    def events(self) -> Any:
        """Events resource accessor (lazy import)."""
        return self._resource("events", "EventsResource")

    @property
    def channels(self) -> Any:
        """Channels resource accessor (lazy import)."""
        return self._resource("channels", "ChannelsResource")

    @property
    def apps(self) -> Any:
        """Apps resource accessor (lazy import)."""
        return self._resource("apps", "AppsResource")

    @property
    def environments(self) -> Any:
        """Environments resource accessor (lazy import)."""
        return self._resource("environments", "EnvironmentsResource")

    @property
    def webhooks(self) -> Any:
        """Webhooks resource accessor (lazy import)."""
        return self._resource("webhooks", "WebhooksResource")

    @property
    def traces(self) -> Any:
        """Traces resource accessor (lazy import)."""
        return self._resource("traces", "TracesResource")

    @property
    def api_keys(self) -> Any:
        """API keys resource accessor (lazy import)."""
        return self._resource("api_keys", "ApiKeysResource")

    @property
    def organizations(self) -> Any:
        """Organizations resource accessor (lazy import)."""
        return self._resource("organizations", "OrganizationsResource")

    def connect_realtime(self, **kwargs: Any) -> Any:
        """Open a realtime (MQTT) connection.

        Args:
            **kwargs: Forwarded to
                :class:`axonpush.realtime.mqtt.RealtimeClient`.

        Returns:
            A connected ``RealtimeClient`` instance.
        """
        from axonpush.realtime.mqtt import RealtimeClient

        rt = RealtimeClient(self, **kwargs)
        rt.connect()
        return rt


class AsyncAxonPush:
    """Asynchronous AxonPush client.

    Mirrors :class:`AxonPush` exactly; resource accessors return ``Async*``
    classes and :meth:`close` is a coroutine.
    """

    def __init__(
        self,
        *,
        api_key: str | SecretStr | None = None,
        tenant_id: str | None = None,
        base_url: str | HttpUrl | None = None,
        environment: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        fail_open: bool | None = None,
    ) -> None:
        self._settings = _build_settings(
            api_key=api_key,
            tenant_id=tenant_id,
            base_url=base_url,
            environment=environment,
            timeout=timeout,
            max_retries=max_retries,
            fail_open=fail_open,
        )
        self._client: AuthenticatedClient = build_async_client(self._settings)
        self._closed = False

    @property
    def environment(self) -> str | None:
        """Return the configured environment label, or ``None`` if unset."""
        return self._settings.environment

    @property
    def fail_open(self) -> bool:
        """Whether the facade swallows :class:`APIConnectionError`."""
        return self._settings.fail_open

    @property
    def settings(self) -> Settings:
        """The frozen :class:`Settings` powering this client."""
        return self._settings

    @property
    def http(self) -> "AuthenticatedClient":
        """The underlying generated HTTP client (for resource modules)."""
        return self._client

    async def _invoke(
        self,
        op: Any,
        *,
        _coerce: Callable[[Any], R] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call ``op.asyncio_detailed`` through the retry layer.

        See :meth:`AxonPush._invoke` for behaviour.
        """
        try:
            response = await call_with_retries_async(
                op,
                client=self._client,
                max_retries=self._settings.max_retries,
                **kwargs,
            )
        except APIConnectionError:
            if self._settings.fail_open:
                return None
            raise
        parsed = getattr(response, "parsed", response)
        if _coerce is not None and parsed is not None:
            return _coerce(parsed)
        return parsed

    async def close(self) -> None:
        """Close the underlying HTTP client. Idempotent."""
        if self._closed:
            return
        await self._client.get_async_httpx_client().aclose()
        self._closed = True

    aclose = close

    async def __aenter__(self) -> "AsyncAxonPush":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    def _resource(self, module_name: str, class_name: str) -> Any:
        import importlib

        module = importlib.import_module(f"axonpush.resources.{module_name}")
        return getattr(module, class_name)(self)

    @property
    def events(self) -> Any:
        """Events resource accessor (lazy import)."""
        return self._resource("events", "AsyncEventsResource")

    @property
    def channels(self) -> Any:
        """Channels resource accessor (lazy import)."""
        return self._resource("channels", "AsyncChannelsResource")

    @property
    def apps(self) -> Any:
        """Apps resource accessor (lazy import)."""
        return self._resource("apps", "AsyncAppsResource")

    @property
    def environments(self) -> Any:
        """Environments resource accessor (lazy import)."""
        return self._resource("environments", "AsyncEnvironmentsResource")

    @property
    def webhooks(self) -> Any:
        """Webhooks resource accessor (lazy import)."""
        return self._resource("webhooks", "AsyncWebhooksResource")

    @property
    def traces(self) -> Any:
        """Traces resource accessor (lazy import)."""
        return self._resource("traces", "AsyncTracesResource")

    @property
    def api_keys(self) -> Any:
        """API keys resource accessor (lazy import)."""
        return self._resource("api_keys", "AsyncApiKeysResource")

    @property
    def organizations(self) -> Any:
        """Organizations resource accessor (lazy import)."""
        return self._resource("organizations", "AsyncOrganizationsResource")

    async def connect_realtime(self, **kwargs: Any) -> Any:
        """Open an asynchronous realtime (MQTT) connection.

        Args:
            **kwargs: Forwarded to
                :class:`axonpush.realtime.mqtt_async.AsyncRealtimeClient`.

        Returns:
            A connected ``AsyncRealtimeClient`` instance.
        """
        from axonpush.realtime.mqtt_async import AsyncRealtimeClient

        rt = AsyncRealtimeClient(self, **kwargs)
        await rt.connect()
        return rt


__all__ = ["AsyncAxonPush", "AxonPush"]
