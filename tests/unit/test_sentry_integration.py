"""Unit tests for ``install_sentry`` — verifies DSN construction, env-var
fallbacks, precedence of the environment detector, and the Sentry SDK
contract (single ``sentry_sdk.init`` call with the right kwargs).

These tests do NOT require ``sentry-sdk`` to be installed. A stub module is
injected via ``sys.modules`` so the integration's ``import sentry_sdk`` call
binds to the stub."""

from __future__ import annotations

import sys
import types

import pytest

from axonpush.integrations.sentry import build_dsn, install_sentry


@pytest.fixture()
def sentry_stub(monkeypatch):
    """Install a fake ``sentry_sdk`` module that records ``init()`` calls.

    Without this, ``install_sentry`` raises ImportError on systems that don't
    have sentry-sdk installed — these tests must work either way."""
    stub = types.ModuleType("sentry_sdk")
    calls: list[dict] = []

    def fake_init(**kwargs):
        calls.append(kwargs)

    stub.init = fake_init  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sentry_sdk", stub)
    return calls


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Prevent the host's real env vars from leaking into the env detector."""
    for k in (
        "AXONPUSH_API_KEY",
        "AXONPUSH_CHANNEL_ID",
        "AXONPUSH_HOST",
        "AXONPUSH_ENVIRONMENT",
        "SENTRY_ENVIRONMENT",
        "APP_ENV",
        "ENV",
    ):
        monkeypatch.delenv(k, raising=False)


class TestBuildDsn:
    def test_https_for_production_host(self):
        assert build_dsn("ak_abc", 42, "api.axonpush.xyz") == "https://ak_abc@api.axonpush.xyz/42"

    def test_http_for_localhost(self):
        assert build_dsn("ak_abc", 42, "localhost:3000") == "http://ak_abc@localhost:3000/42"

    def test_http_for_127_loopback(self):
        assert build_dsn("ak_abc", 42, "127.0.0.1:3000") == "http://ak_abc@127.0.0.1:3000/42"


class TestInstallSentry:
    def test_builds_dsn_from_kwargs(self, sentry_stub):
        install_sentry(api_key="ak_abc", channel_id=42)
        assert len(sentry_stub) == 1
        assert sentry_stub[0]["dsn"] == "https://ak_abc@api.axonpush.xyz/42"

    def test_explicit_dsn_bypasses_builder(self, sentry_stub):
        """Passing ``dsn=`` must short-circuit the api_key/channel_id/host
        lookup — caller takes full responsibility for the DSN."""
        install_sentry(dsn="https://custom@sentry.io/1")
        assert sentry_stub[0]["dsn"] == "https://custom@sentry.io/1"

    def test_env_vars_fill_in_missing_kwargs(self, sentry_stub, monkeypatch):
        monkeypatch.setenv("AXONPUSH_API_KEY", "ak_from_env")
        monkeypatch.setenv("AXONPUSH_CHANNEL_ID", "7")
        install_sentry()
        assert sentry_stub[0]["dsn"] == "https://ak_from_env@api.axonpush.xyz/7"

    def test_custom_host_env_var(self, sentry_stub, monkeypatch):
        monkeypatch.setenv("AXONPUSH_API_KEY", "ak_x")
        monkeypatch.setenv("AXONPUSH_CHANNEL_ID", "1")
        monkeypatch.setenv("AXONPUSH_HOST", "localhost:3000")
        install_sentry()
        assert sentry_stub[0]["dsn"] == "http://ak_x@localhost:3000/1"

    def test_missing_credentials_raises(self, sentry_stub):
        with pytest.raises(ValueError, match="api_key and channel_id"):
            install_sentry()

    def test_environment_and_release_forwarded(self, sentry_stub):
        install_sentry(
            api_key="ak_x",
            channel_id=1,
            environment="production",
            release="my-app@1.2.3",
        )
        assert sentry_stub[0]["environment"] == "production"
        assert sentry_stub[0]["release"] == "my-app@1.2.3"

    def test_environment_auto_detected_from_env_vars(self, sentry_stub, monkeypatch):
        """Same precedence as the AxonPush client:
        AXONPUSH_ENVIRONMENT > SENTRY_ENVIRONMENT > APP_ENV > ENV."""
        monkeypatch.setenv("ENV", "env-val")
        monkeypatch.setenv("APP_ENV", "app-env-val")
        monkeypatch.setenv("SENTRY_ENVIRONMENT", "sentry-val")
        monkeypatch.setenv("AXONPUSH_ENVIRONMENT", "axonpush-val")
        install_sentry(api_key="ak_x", channel_id=1)
        assert sentry_stub[0]["environment"] == "axonpush-val"

    def test_environment_not_set_when_nothing_detected(self, sentry_stub):
        install_sentry(api_key="ak_x", channel_id=1)
        assert "environment" not in sentry_stub[0]

    def test_extra_kwargs_passed_through_to_sentry_init(self, sentry_stub):
        """``**sentry_init_kwargs`` catches everything not explicitly named —
        these are the knobs users will want to tune (sample rates, integrations,
        transport options)."""
        install_sentry(
            api_key="ak_x",
            channel_id=1,
            traces_sample_rate=0.25,
            send_default_pii=False,
            max_breadcrumbs=50,
        )
        call = sentry_stub[0]
        assert call["traces_sample_rate"] == 0.25
        assert call["send_default_pii"] is False
        assert call["max_breadcrumbs"] == 50

    def test_explicit_environment_beats_env_var(self, sentry_stub, monkeypatch):
        monkeypatch.setenv("AXONPUSH_ENVIRONMENT", "from-env")
        install_sentry(api_key="ak_x", channel_id=1, environment="explicit")
        assert sentry_stub[0]["environment"] == "explicit"


class TestMissingSentrySdk:
    def test_import_error_has_actionable_message(self, monkeypatch):
        """If sentry-sdk isn't installed, install_sentry must raise an
        ImportError with install instructions — not a cryptic ModuleNotFoundError."""
        monkeypatch.setitem(sys.modules, "sentry_sdk", None)  # poison the import
        with pytest.raises(ImportError, match="pip install sentry-sdk"):
            install_sentry(api_key="ak_x", channel_id=1)
