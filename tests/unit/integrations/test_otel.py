"""Unit tests for the OpenTelemetry SpanExporter."""

from __future__ import annotations

import pytest

pytest.importorskip("opentelemetry.sdk.trace")

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import (  # noqa: E402
    SimpleSpanProcessor,
    SpanExportResult,
)

from axonpush.integrations.otel import AxonPushSpanExporter  # noqa: E402

from .conftest import FakeSyncClient  # noqa: E402


def _provider_with(exporter: AxonPushSpanExporter) -> TracerProvider:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider


class TestOTelExporter:
    def test_emits_app_span_event(self, fake_sync_client: FakeSyncClient) -> None:
        exporter = AxonPushSpanExporter(
            client=fake_sync_client,
            channel_id="ch_x",
            service_name="myapp",
            mode="sync",
        )
        provider = _provider_with(exporter)
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("POST /chat") as span:
            span.set_attribute("http.method", "POST")
        provider.shutdown()
        assert len(fake_sync_client.events.calls) == 1
        call = fake_sync_client.events.calls[0]
        assert call["identifier"] == "POST /chat"
        assert call["event_type"].value == "app.span"
        assert call["channel_id"] == "ch_x"
        assert call["payload"]["name"] == "POST /chat"
        assert call["payload"]["attributes"]["http.method"] == "POST"
        assert call["metadata"]["framework"] == "opentelemetry"

    def test_parent_span_id_propagated(self, fake_sync_client: FakeSyncClient) -> None:
        exporter = AxonPushSpanExporter(client=fake_sync_client, channel_id="ch_x", mode="sync")
        provider = _provider_with(exporter)
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("parent"):
            with tracer.start_as_current_span("child"):
                pass
        provider.shutdown()
        # Child exports first (SimpleSpanProcessor flushes on end)
        assert len(fake_sync_client.events.calls) == 2
        child = fake_sync_client.events.calls[0]
        parent = fake_sync_client.events.calls[1]
        assert "parent_event_id" in child
        assert child["parent_event_id"] == parent["span_id"]
        assert "parent_event_id" not in parent

    def test_invalid_mode_rejected(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.raises(ValueError, match="mode must be"):
            AxonPushSpanExporter(
                client=fake_sync_client,
                channel_id="ch_x",
                mode="bogus",  # type: ignore[arg-type]
            )

    def test_int_channel_id_emits_deprecation(self, fake_sync_client: FakeSyncClient) -> None:
        with pytest.warns(DeprecationWarning):
            AxonPushSpanExporter(client=fake_sync_client, channel_id=99, mode="sync")

    def test_export_failure_returned_as_failure(self, fake_sync_client: FakeSyncClient) -> None:
        # We have to inject a faulty export by feeding the exporter a span
        # whose attribute access raises. Easiest: monkeypatch _export_one.
        exporter = AxonPushSpanExporter(client=fake_sync_client, channel_id="ch_x", mode="sync")

        class BoomSpan:
            def __getattr__(self, name: str) -> object:
                raise RuntimeError("boom")

        result = exporter.export([BoomSpan()])  # type: ignore[list-item]
        assert result is SpanExportResult.FAILURE

    def test_environment_propagated(self, fake_sync_client: FakeSyncClient) -> None:
        exporter = AxonPushSpanExporter(
            client=fake_sync_client,
            channel_id="ch_x",
            environment="staging",
            mode="sync",
        )
        provider = _provider_with(exporter)
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("x"):
            pass
        provider.shutdown()
        assert fake_sync_client.events.calls[0]["environment"] == "staging"

    def test_force_flush_returns_true(self, fake_sync_client: FakeSyncClient) -> None:
        exporter = AxonPushSpanExporter(client=fake_sync_client, channel_id="ch_x", mode="sync")
        assert exporter.force_flush(1) is True
