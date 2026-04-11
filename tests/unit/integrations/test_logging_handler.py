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
        """Each Python level → expected OTel severity number.

        We also assert that ``route.call_count`` grows by exactly 1 per
        iteration. Without this guard, a silently filtered level (e.g. if
        the handler ever started dropping DEBUG) would leave us reading the
        previous iteration's body and the test would pass against stale data.
        """
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
            expected_calls = 0
            for log_fn, msg, expected_num, expected_text in cases:
                log_fn(msg)
                expected_calls += 1
                assert route.call_count == expected_calls, (
                    f"expected handler to emit a request for {expected_text}, "
                    f"but route.call_count is {route.call_count}"
                )
                body = _last_body(route)
                assert body["payload"]["severityNumber"] == expected_num
                assert body["payload"]["severityText"] == expected_text
                assert body["payload"]["body"] == msg

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
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            # Silence handleError's noisy stderr fallback for this test
            handler.handleError = lambda record: None  # type: ignore[method-assign]
            isolated_logger.addHandler(handler)
            try:
                isolated_logger.error("test")
            except Exception as exc:
                pytest.fail(
                    f"AxonPushLoggingHandler.emit() raised {type(exc).__name__}: "
                    f"{exc}. emit() must swallow all exceptions per the "
                    f"logging.Handler contract."
                )

    def test_resource_omitted_when_no_service_info(self, mock_router, isolated_logger):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            isolated_logger.addHandler(
                AxonPushLoggingHandler(client=c, channel_id=5)
            )
            isolated_logger.info("plain")
        body = _last_body(route)
        assert "resource" not in body["payload"]


def _make_record(name: str, msg: str = "x") -> logging.LogRecord:
    """Construct a minimal LogRecord for filter-path tests."""
    return logging.LogRecord(
        name=name,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )


class TestSelfRecursionFilter:
    """The handler must NOT ship records that would create an infinite loop.

    Publishing an event triggers an httpx HTTP request; httpx itself logs
    that request at INFO level via the ``httpx`` stdlib logger. Without a
    filter, every publish would queue another publish, and the channel
    would fill with "HTTP Request: POST /event" echoes. The always-on
    excluded prefixes are ``httpx``, ``httpcore``, ``axonpush``.
    """

    def test_httpx_records_are_dropped(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            handler.handle(_make_record("httpx"))
            handler.handle(_make_record("httpx._client"))
        assert not route.called

    def test_httpcore_records_are_dropped(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            handler.handle(_make_record("httpcore.connection"))
            handler.handle(_make_record("httpcore.http11"))
        assert not route.called

    def test_axonpush_internal_logger_is_dropped_exact_match(self, mock_router):
        """The SDK's own ``axonpush`` logger must be blocked to prevent
        feedback when ``_http.py`` / ``client.py`` log fail-open warnings."""
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            handler.handle(_make_record("axonpush"))
        assert not route.called

    def test_axonpush_user_namespace_is_allowed(self, mock_router):
        """User code that puts its loggers in the ``axonpush.*`` namespace
        (e.g. a plugin, or the existing test fixture) must still ship.

        The ``axonpush`` default is matched by EQUALITY, not prefix, so
        ``axonpush.plugins.foo`` / ``axonpush.test.bar`` pass through."""
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            handler.handle(_make_record("axonpush.plugins.foo"))
            handler.handle(_make_record("axonpush.test.bar"))
        assert route.call_count == 2

    def test_user_records_still_flow_through(self, mock_router):
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(client=c, channel_id=5)
            handler.handle(_make_record("my_app.users"))
        assert route.call_count == 1

    def test_user_supplied_exclusions_are_additive(self, mock_router):
        """User-supplied prefixes are added on top of the defaults."""
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(
                client=c,
                channel_id=5,
                exclude_loggers=["werkzeug", "my_app.noisy"],
            )
            handler.handle(_make_record("werkzeug"))
            handler.handle(_make_record("my_app.noisy.subsystem"))
        assert not route.called

    def test_user_exclusions_cannot_disable_defaults(self, mock_router):
        """Passing a custom list must NOT re-enable the feedback loop.

        Even if a user passes a custom ``exclude_loggers`` list that does
        not include ``httpx`` / ``httpcore`` / ``axonpush``, those defaults
        must still be enforced — the additive semantics are load-bearing.
        """
        route = mock_router.post("/event").mock(return_value=_ack())
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            handler = AxonPushLoggingHandler(
                client=c,
                channel_id=5,
                exclude_loggers=["my_app.noisy"],
            )
            handler.handle(_make_record("httpx"))
            handler.handle(_make_record("httpcore"))
            handler.handle(_make_record("axonpush"))
        assert not route.called


class TestDictConfigConstructor:
    """AxonPushLoggingHandler must be usable via logging.config.dictConfig.

    Django uses dictConfig in ``settings.py``; dictConfig only supports
    primitive kwargs (strings/ints), so a pre-built ``client`` instance
    can't be passed. The constructor accepts ``api_key`` / ``tenant_id`` /
    ``base_url`` kwargs OR reads them from environment variables, and
    fails fast with an actionable error if neither path yields creds.
    """

    def test_builds_client_from_credential_kwargs(
        self, mock_router, isolated_logger
    ):
        route = mock_router.post("/event").mock(return_value=_ack())
        handler = AxonPushLoggingHandler(
            api_key=API_KEY,
            tenant_id=TENANT_ID,
            base_url=BASE_URL,
            channel_id=5,
            service_name="dictconfig-test",
        )
        isolated_logger.addHandler(handler)
        isolated_logger.info("hello")
        assert route.called
        body = _last_body(route)
        assert body["payload"]["resource"]["service.name"] == "dictconfig-test"

    def test_builds_client_from_env_vars(
        self, mock_router, isolated_logger, monkeypatch
    ):
        monkeypatch.setenv("AXONPUSH_API_KEY", API_KEY)
        monkeypatch.setenv("AXONPUSH_TENANT_ID", TENANT_ID)
        monkeypatch.setenv("AXONPUSH_BASE_URL", BASE_URL)
        route = mock_router.post("/event").mock(return_value=_ack())
        handler = AxonPushLoggingHandler(channel_id=5)
        isolated_logger.addHandler(handler)
        isolated_logger.info("env-test")
        assert route.called

    def test_missing_credentials_raises(self, monkeypatch):
        monkeypatch.delenv("AXONPUSH_API_KEY", raising=False)
        monkeypatch.delenv("AXONPUSH_TENANT_ID", raising=False)
        monkeypatch.delenv("AXONPUSH_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="provide either client="):
            AxonPushLoggingHandler(channel_id=5)

    def test_client_and_credentials_conflict_raises(self):
        with AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL) as c:
            with pytest.raises(ValueError, match="not both"):
                AxonPushLoggingHandler(
                    client=c,
                    api_key="ak_other",
                    tenant_id="2",
                    channel_id=5,
                )

    def test_via_logging_dict_config(self, mock_router, monkeypatch):
        """End-to-end: build the handler through ``logging.config.dictConfig``.

        This is the exact pattern a Django ``LOGGING`` setting would use:
        dictConfig passes only primitive kwargs, so a pre-built client is
        not available — the handler must resolve credentials itself.
        """
        import logging.config

        monkeypatch.setenv("AXONPUSH_API_KEY", API_KEY)
        monkeypatch.setenv("AXONPUSH_TENANT_ID", TENANT_ID)
        monkeypatch.setenv("AXONPUSH_BASE_URL", BASE_URL)
        route = mock_router.post("/event").mock(return_value=_ack())

        name = f"axonpush.test.dictconfig.{id(object())}"
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "handlers": {
                    "axonpush": {
                        "class": "axonpush.integrations.logging_handler.AxonPushLoggingHandler",
                        "channel_id": 5,
                        "service_name": "django-style",
                    },
                },
                "loggers": {
                    name: {
                        "handlers": ["axonpush"],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
            }
        )
        try:
            logging.getLogger(name).info("django hello")
            assert route.called
            body = _last_body(route)
            assert body["payload"]["resource"]["service.name"] == "django-style"
        finally:
            lg = logging.getLogger(name)
            for h in list(lg.handlers):
                lg.removeHandler(h)
