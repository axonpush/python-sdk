"""Unit tests for ``axonpush._internal.transport``."""

from __future__ import annotations

from typing import Any

import httpx
import pytest
import respx
from pydantic import HttpUrl, SecretStr

from axonpush._config import Settings
from axonpush._internal.transport import (
    build_async_client,
    build_sync_client,
    call_with_retries_async,
    call_with_retries_sync,
)
from axonpush._tracing import TraceContext, set_current_trace
from axonpush.exceptions import (
    APIConnectionError,
    AuthenticationError,
    AxonPushError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "api_key": SecretStr("ak_test"),
        "tenant_id": "tnt_42",
        "base_url": HttpUrl("http://api.example.test"),
        "environment": "production",
        "timeout": 5.0,
        "max_retries": 0,
        "fail_open": False,
    }
    base.update(overrides)
    return Settings(**base)


class TestBuildSyncClient:
    def test_request_carries_auth_tenant_environment_headers(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test", assert_all_called=True) as router:
            route = router.get("/health").mock(return_value=httpx.Response(200, json={}))
            client.get_httpx_client().get("/health")

        sent = route.calls.last.request.headers
        assert sent["x-api-key"] == "ak_test"
        assert sent["x-tenant-id"] == "tnt_42"
        assert sent["x-axonpush-environment"] == "production"
        assert "x-axonpush-trace-id" not in sent
        client.get_httpx_client().close()

    def test_trace_id_header_injected_when_context_active(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        ctx = TraceContext(trace_id="11111111-1111-4111-8111-111111111111")
        token = set_current_trace(ctx)
        try:
            with respx.mock(base_url="http://api.example.test") as router:
                route = router.get("/health").mock(return_value=httpx.Response(200, json={}))
                client.get_httpx_client().get("/health")
            sent = route.calls.last.request.headers
            assert sent["x-axonpush-trace-id"] == ctx.trace_id
        finally:
            from axonpush._tracing import _clear_current_trace

            _clear_current_trace(token)
            client.get_httpx_client().close()

    def test_401_maps_to_authentication_error(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(
                return_value=httpx.Response(
                    401,
                    json={"code": "unauthorized", "message": "bad key"},
                    headers={"X-Request-Id": "req-1"},
                )
            )
            with pytest.raises(AuthenticationError) as exc:
                client.get_httpx_client().get("/health")
        assert exc.value.status_code == 401
        assert exc.value.code == "unauthorized"
        assert exc.value.message == "bad key"
        assert exc.value.request_id == "req-1"
        client.get_httpx_client().close()

    def test_404_maps_to_not_found(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(
                return_value=httpx.Response(404, json={"message": "missing"})
            )
            with pytest.raises(NotFoundError):
                client.get_httpx_client().get("/health")
        client.get_httpx_client().close()

    def test_422_maps_to_validation_error(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(
                return_value=httpx.Response(422, json={"message": "bad body"})
            )
            with pytest.raises(ValidationError):
                client.get_httpx_client().get("/health")
        client.get_httpx_client().close()

    def test_429_maps_to_rate_limit_with_retry_after(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(
                return_value=httpx.Response(
                    429,
                    headers={"Retry-After": "2.5"},
                    json={"message": "slow down"},
                )
            )
            with pytest.raises(RateLimitError) as exc:
                client.get_httpx_client().get("/health")
        assert exc.value.retry_after == 2.5
        client.get_httpx_client().close()

    def test_503_maps_to_server_error(self) -> None:
        settings = _settings()
        client = build_sync_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(return_value=httpx.Response(503, json={"message": "down"}))
            with pytest.raises(ServerError):
                client.get_httpx_client().get("/health")
        client.get_httpx_client().close()


class TestBuildAsyncClient:
    async def test_async_request_carries_headers(self) -> None:
        settings = _settings()
        client = build_async_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            route = router.get("/health").mock(return_value=httpx.Response(200, json={}))
            await client.get_async_httpx_client().get("/health")
        sent = route.calls.last.request.headers
        assert sent["x-api-key"] == "ak_test"
        assert sent["x-tenant-id"] == "tnt_42"
        assert sent["x-axonpush-environment"] == "production"
        await client.get_async_httpx_client().aclose()

    async def test_async_401_maps_to_authentication_error(self) -> None:
        settings = _settings()
        client = build_async_client(settings)
        with respx.mock(base_url="http://api.example.test") as router:
            router.get("/health").mock(return_value=httpx.Response(401, json={"message": "nope"}))
            with pytest.raises(AuthenticationError):
                await client.get_async_httpx_client().get("/health")
        await client.get_async_httpx_client().aclose()


class _Op:
    """Stand-in for a generated op module."""

    def __init__(self, results: list[Any]) -> None:
        self._results = list(results)
        self.calls = 0

    def sync_detailed(self, **kwargs: Any) -> Any:
        self.calls += 1
        item = self._results.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    async def asyncio_detailed(self, **kwargs: Any) -> Any:
        self.calls += 1
        item = self._results.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


class TestCallWithRetriesSync:
    def test_returns_response_on_first_success(self) -> None:
        op = _Op(["ok"])
        result = call_with_retries_sync(op, max_retries=3)
        assert result == "ok"
        assert op.calls == 1

    def test_retries_on_server_error_then_succeeds(self) -> None:
        op = _Op([ServerError("boom", status_code=503), "ok"])
        sleeps: list[float] = []
        result = call_with_retries_sync(op, max_retries=3, sleep=lambda s: sleeps.append(s))
        assert result == "ok"
        assert op.calls == 2
        assert sleeps == [0.25]

    def test_backoff_schedule(self) -> None:
        op = _Op(
            [
                ServerError("a"),
                ServerError("b"),
                ServerError("c"),
                ServerError("d"),
                ServerError("e"),
                "ok",
            ]
        )
        sleeps: list[float] = []
        result = call_with_retries_sync(op, max_retries=5, sleep=lambda s: sleeps.append(s))
        assert result == "ok"
        assert sleeps == [0.25, 0.5, 1.0, 2.0, 4.0]

    def test_rate_limit_uses_retry_after(self) -> None:
        op = _Op([RateLimitError("slow", retry_after=7.0), "ok"])
        sleeps: list[float] = []
        result = call_with_retries_sync(op, max_retries=3, sleep=lambda s: sleeps.append(s))
        assert result == "ok"
        assert sleeps == [7.0]

    def test_transport_error_wrapped_as_api_connection_error(self) -> None:
        op = _Op([httpx.ConnectError("dns fail")])
        with pytest.raises(APIConnectionError):
            call_with_retries_sync(op, max_retries=0, sleep=lambda s: None)

    def test_transport_error_is_retried(self) -> None:
        op = _Op([httpx.ConnectError("dns fail"), "ok"])
        result = call_with_retries_sync(op, max_retries=2, sleep=lambda s: None)
        assert result == "ok"
        assert op.calls == 2

    def test_non_retryable_error_propagates_immediately(self) -> None:
        op = _Op([AuthenticationError("nope", status_code=401)])
        with pytest.raises(AuthenticationError):
            call_with_retries_sync(op, max_retries=5, sleep=lambda s: None)
        assert op.calls == 1

    def test_exhausts_retries_and_raises_last(self) -> None:
        op = _Op([ServerError("a"), ServerError("b"), ServerError("c")])
        with pytest.raises(ServerError) as exc:
            call_with_retries_sync(op, max_retries=2, sleep=lambda s: None)
        assert str(exc.value) == "c"
        assert op.calls == 3


class TestCallWithRetriesAsync:
    async def test_async_retry_on_server_error(self) -> None:
        op = _Op([ServerError("boom", status_code=503), "ok"])
        sleeps: list[float] = []

        async def fake_sleep(s: float) -> None:
            sleeps.append(s)

        result = await call_with_retries_async(op, max_retries=2, sleep=fake_sleep)
        assert result == "ok"
        assert sleeps == [0.25]

    async def test_async_transport_error_wrapped(self) -> None:
        op = _Op([httpx.ConnectError("net fail")])

        async def fake_sleep(s: float) -> None:
            pass

        with pytest.raises(APIConnectionError):
            await call_with_retries_async(op, max_retries=0, sleep=fake_sleep)

    async def test_async_non_retryable_propagates(self) -> None:
        op = _Op([AuthenticationError("nope", status_code=401)])

        async def fake_sleep(s: float) -> None:
            pass

        with pytest.raises(AuthenticationError):
            await call_with_retries_async(op, max_retries=5, sleep=fake_sleep)

    async def test_async_exhausts_retries(self) -> None:
        op = _Op([ServerError("a"), ServerError("b")])

        async def fake_sleep(s: float) -> None:
            pass

        with pytest.raises(AxonPushError):
            await call_with_retries_async(op, max_retries=1, sleep=fake_sleep)
        assert op.calls == 2
