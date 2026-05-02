"""Unit tests for the AxonPush facade — no backend required."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from axonpush._config import Settings
from axonpush.client import AsyncAxonPush, AxonPush
from axonpush.exceptions import (
    APIConnectionError,
    AuthenticationError,
    NotFoundError,
)


class _FakeResponse:
    def __init__(self, parsed: Any) -> None:
        self.parsed = parsed


class TestSyncFacadeConstruction:
    def test_construction_kwargs_only(self) -> None:
        c = AxonPush(api_key="ak_x", tenant_id="42", base_url="http://localhost:3000")
        assert c.settings.api_key is not None
        assert c.settings.api_key.get_secret_value() == "ak_x"
        assert c.settings.tenant_id == "42"
        c.close()

    def test_construction_requires_kwargs(self) -> None:
        with pytest.raises(TypeError):
            AxonPush("ak_x", "42")  # type: ignore[misc]

    def test_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for k in (
            "AXONPUSH_API_KEY",
            "AXONPUSH_TENANT_ID",
            "AXONPUSH_BASE_URL",
            "AXONPUSH_ENVIRONMENT",
            "AXONPUSH_TIMEOUT",
            "AXONPUSH_MAX_RETRIES",
            "AXONPUSH_FAIL_OPEN",
        ):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("AXONPUSH_API_KEY", "env_key")
        monkeypatch.setenv("AXONPUSH_TENANT_ID", "env_tnt")
        monkeypatch.setenv("AXONPUSH_BASE_URL", "http://envhost:9000")
        monkeypatch.setenv("AXONPUSH_ENVIRONMENT", "staging")
        monkeypatch.setenv("AXONPUSH_TIMEOUT", "12.5")
        monkeypatch.setenv("AXONPUSH_MAX_RETRIES", "7")
        monkeypatch.setenv("AXONPUSH_FAIL_OPEN", "true")

        c = AxonPush()
        assert c.settings.api_key is not None
        assert c.settings.api_key.get_secret_value() == "env_key"
        assert c.settings.tenant_id == "env_tnt"
        assert str(c.settings.base_url).rstrip("/") == "http://envhost:9000"
        assert c.settings.environment == "staging"
        assert c.settings.timeout == 12.5
        assert c.settings.max_retries == 7
        assert c.settings.fail_open is True
        c.close()

    def test_kwargs_override_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AXONPUSH_API_KEY", "env_key")
        monkeypatch.setenv("AXONPUSH_TENANT_ID", "env_tnt")
        monkeypatch.setenv("AXONPUSH_ENVIRONMENT", "staging")
        c = AxonPush(api_key="kwarg_key", environment="production")
        assert c.settings.api_key is not None
        assert c.settings.api_key.get_secret_value() == "kwarg_key"
        assert c.settings.tenant_id == "env_tnt"
        assert c.settings.environment == "production"
        c.close()

    def test_environment_property(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test", environment="prod")
        assert c.environment == "prod"
        c.close()

    def test_secret_str_passthrough(self) -> None:
        c = AxonPush(api_key=SecretStr("secret"), tenant_id="1")
        assert c.settings.api_key is not None
        assert c.settings.api_key.get_secret_value() == "secret"
        c.close()


class TestSyncFacadeBehaviour:
    def test_context_manager_closes_http_client(self) -> None:
        with AxonPush(api_key="x", tenant_id="1", base_url="http://x.test") as c:
            httpx_client = c.http.get_httpx_client()
            assert not httpx_client.is_closed
        assert httpx_client.is_closed

    def test_close_is_idempotent(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        c.close()
        c.close()

    def test_invoke_returns_parsed_on_success(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        with patch(
            "axonpush.client.call_with_retries_sync",
            return_value=_FakeResponse(parsed={"id": "abc"}),
        ):
            result = c._invoke(object())
        assert result == {"id": "abc"}
        c.close()

    def test_invoke_applies_coerce(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        with patch(
            "axonpush.client.call_with_retries_sync",
            return_value=_FakeResponse(parsed={"id": "abc"}),
        ):
            result = c._invoke(object(), _coerce=lambda p: p["id"])
        assert result == "abc"
        c.close()

    def test_fail_open_swallows_connection_error(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test", fail_open=True)
        with patch(
            "axonpush.client.call_with_retries_sync",
            side_effect=APIConnectionError("nope"),
        ):
            result = c._invoke(object())
        assert result is None
        c.close()

    def test_fail_open_does_not_swallow_other_errors(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test", fail_open=True)
        with patch(
            "axonpush.client.call_with_retries_sync",
            side_effect=AuthenticationError("nope", status_code=401),
        ):
            with pytest.raises(AuthenticationError):
                c._invoke(object())
        c.close()

    def test_fail_open_false_propagates_connection_error(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test", fail_open=False)
        with patch(
            "axonpush.client.call_with_retries_sync",
            side_effect=APIConnectionError("nope"),
        ):
            with pytest.raises(APIConnectionError):
                c._invoke(object())
        c.close()

    def test_fail_open_default_is_false(self) -> None:
        c = AxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        assert c.fail_open is False
        c.close()

    def test_invoke_passes_max_retries_from_settings(self) -> None:
        c = AxonPush(
            api_key="x",
            tenant_id="1",
            base_url="http://x.test",
            max_retries=11,
        )
        with patch(
            "axonpush.client.call_with_retries_sync",
            return_value=_FakeResponse(parsed=None),
        ) as mocked:
            c._invoke(object(), foo="bar")
        assert mocked.call_args.kwargs["max_retries"] == 11
        assert mocked.call_args.kwargs["foo"] == "bar"
        assert mocked.call_args.kwargs["client"] is c.http
        c.close()


class TestSettingsModel:
    def test_settings_is_frozen(self) -> None:
        s = Settings(api_key=SecretStr("x"))
        with pytest.raises(Exception):
            s.api_key = SecretStr("y")  # type: ignore[misc]

    def test_settings_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for k in (
            "AXONPUSH_API_KEY",
            "AXONPUSH_TENANT_ID",
            "AXONPUSH_BASE_URL",
            "AXONPUSH_ENVIRONMENT",
            "AXONPUSH_TIMEOUT",
            "AXONPUSH_MAX_RETRIES",
            "AXONPUSH_FAIL_OPEN",
        ):
            monkeypatch.delenv(k, raising=False)
        s = Settings()
        assert s.timeout == 30.0
        assert s.max_retries == 3
        assert s.fail_open is False
        assert str(s.base_url).rstrip("/") == "http://localhost:3000"


class TestAsyncFacade:
    async def test_construction(self) -> None:
        c = AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        assert c.settings.tenant_id == "1"
        await c.close()

    async def test_context_manager_closes_http_client(self) -> None:
        async with AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test") as c:
            httpx_client = c.http.get_async_httpx_client()
            assert not httpx_client.is_closed
        assert httpx_client.is_closed

    async def test_aclose_is_idempotent(self) -> None:
        c = AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test")
        await c.close()
        await c.close()

    async def test_invoke_returns_parsed(self) -> None:
        c = AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test")

        async def fake(*args: Any, **kwargs: Any) -> Any:
            return _FakeResponse(parsed={"id": "x"})

        with patch("axonpush.client.call_with_retries_async", side_effect=fake):
            result = await c._invoke(object())
        assert result == {"id": "x"}
        await c.close()

    async def test_async_fail_open_swallows_connection_error(self) -> None:
        c = AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test", fail_open=True)

        async def fake(*args: Any, **kwargs: Any) -> Any:
            raise APIConnectionError("nope")

        with patch("axonpush.client.call_with_retries_async", side_effect=fake):
            result = await c._invoke(object())
        assert result is None
        await c.close()

    async def test_async_fail_open_does_not_swallow_other_errors(self) -> None:
        c = AsyncAxonPush(api_key="x", tenant_id="1", base_url="http://x.test", fail_open=True)

        async def fake(*args: Any, **kwargs: Any) -> Any:
            raise NotFoundError("missing", status_code=404)

        with patch("axonpush.client.call_with_retries_async", side_effect=fake):
            with pytest.raises(NotFoundError):
                await c._invoke(object())
        await c.close()


class TestSyncFacadeWire:
    """End-to-end sanity check using respx — confirms the facade composes."""

    def test_unauthorized_response_raises_authentication_error(self) -> None:
        with respx_mock() as router:
            router.get("/health").mock(
                return_value=httpx.Response(401, json={"message": "bad key"})
            )
            with AxonPush(api_key="x", tenant_id="1", base_url="http://x.test", max_retries=0) as c:
                with pytest.raises(AuthenticationError):
                    c.http.get_httpx_client().get("/health")


def respx_mock() -> Any:
    import respx

    return respx.mock(base_url="http://x.test", assert_all_called=False)
