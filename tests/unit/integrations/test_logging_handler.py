"""Unit tests for AxonPushLoggingHandler.

Verifies that stdlib logging records are converted into the OpenTelemetry-shaped
``app.log`` / ``agent.log`` payloads documented in
``axonpush/integrations/_otel_payload.py``. The exact wire shape matters because
the easy-push backend (and any downstream OTel-compatible collector) parses
``severityNumber`` / ``severityText`` / ``body`` / ``attributes`` / ``resource``.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest

from axonpush import AxonPush
from axonpush.integrations.logging_handler import AxonPushLoggingHandler

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "test",
            "payload": {},
            "channel_id": 5,
            "eventType": "app.log",
        },
    )


def _last_body(route) -> dict:
    return json.loads(route.calls.last.request.content)


@pytest.fixture()
def isolated_logger():
    """Yield a fresh logger that won't leak handlers between tests."""
    name = f"axonpush.test.{id(object())}"
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger
    for h in list(logger.handlers):
        logger.removeHandler(h)


class TestLoggingHandlerPayload:
    def test_emits_app_log_event(self, mock_router, isolated_logger):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(
                client=c, channel_id=5, service_name="myapp"
            )
            isolated_logger.addHandler(handler)
            isolated_logger.error("connection refused")

        assert route.called
        body = _last_body(route)
        assert body["channel_id"] == 5
        assert body["eventType"] == "app.log"
        assert body["payload"]["severityText"] == "ERROR"
        assert body["payload"]["severityNumber"] == 17
        assert body["payload"]["body"] == "connection refused"
        assert body["payload"]["resource"]["service.name"] == "myapp"
        assert body["metadata"]["framework"] == "stdlib-logging"

    def test_severity_mapping(self, mock_router, isolated_logger):
        """Each Python level → expected OTel severity number."""
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5)
            )
            cases = [
                (isolated_logger.debug, "d", 5, "DEBUG"),
                (isolated_logger.info, "i", 9, "INFO"),
                (isolated_logger.warning, "w", 13, "WARN"),
                (isolated_logger.error, "e", 17, "ERROR"),
                (isolated_logger.critical, "c", 21, "FATAL"),
            ]
            for log_fn, msg, expected_num, expected_text in cases:
                log_fn(msg)
                body = _last_body(route)
                assert body["payload"]["severityNumber"] == expected_num
                assert body["payload"]["severityText"] == expected_text

    def test_extra_kwargs_become_attributes(self, mock_router, isolated_logger):
        """``logger.error("...", extra={"user_id": 42})`` should land in attributes."""
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5)
            )
            isolated_logger.error("auth fail", extra={"user_id": 42, "ip": "1.2.3.4"})

        attrs = _last_body(route)["payload"]["attributes"]
        # Pydantic _stringify_values keeps int/str/bool/float as-is
        assert attrs["user_id"] == 42
        assert attrs["ip"] == "1.2.3.4"
        # Standard LogRecord-derived attrs are present too
        assert "code.filepath" in attrs
        assert "code.function" in attrs
        assert "code.lineno" in attrs
        assert attrs["logger.name"] == isolated_logger.name

    def test_agent_log_event_type(self, mock_router, isolated_logger):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5, source="agent")
            )
            isolated_logger.info("agent thinking")
        assert _last_body(route)["eventType"] == "agent.log"

    def test_invalid_source_rejected(self):
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            with pytest.raises(ValueError, match="source must be"):
                AxonPushLoggingHandler(client=c, channel_id=5, source="bogus")

    def test_emit_never_raises(self, mock_router, isolated_logger):
        """Per logging.Handler convention, emit() must swallow all exceptions
        — otherwise a flaky log call could crash the user's app."""
        mock_router.post("/event").mock(side_effect=httpx.ConnectError("nope"))
        with AxonPush(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            fail_open=False,  # would normally raise APIConnectionError
        ) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5)
            )
            # Should NOT raise even though the underlying transport would
            isolated_logger.error("test")

    def test_resource_omitted_when_no_service_info(self, mock_router, isolated_logger):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5)
            )
            isolated_logger.info("plain")
        body = _last_body(route)
        assert "resource" not in body["payload"]
