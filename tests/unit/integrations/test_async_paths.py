"""Async-client integration paths.

When a user passes an :class:`AsyncAxonPush` to one of the sync logging
integrations (``AxonPushLoggingHandler``, the loguru sink, the structlog
processor, ``setup_print_capture``, ``AxonPushSpanExporter``), each handler
detects the returned coroutine via ``hasattr(result, "__await__")`` and
schedules it on the running event loop with ``loop.create_task(result)``.

This whole branch — exercised every time someone uses ``AsyncAxonPush``
with a logging integration — was previously **untested**. The handlers
silently swallow scheduling errors via ``except RuntimeError: pass``,
which means a regression here would not surface anywhere except a
production "where are my logs?" ticket.

These tests use AsyncAxonPush from inside an async test (so a loop is
running), trigger one log/span, await ``asyncio.sleep(0)`` to let the
scheduled task run, and assert respx received the request.
"""
from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest

from axonpush import AsyncAxonPush
from axonpush.integrations.logging_handler import AxonPushLoggingHandler

from tests.conftest import API_KEY, BASE_URL, TENANT_ID


def _ack():
    return httpx.Response(
        200,
        json={
            "id": 1,
            "identifier": "x",
            "payload": {},
            "eventType": "app.log",
        },
    )


async def _drain_loop():
    """Yield to the event loop a few times so any tasks scheduled by
    ``loop.create_task()`` get a chance to run their first await."""
    for _ in range(5):
        await asyncio.sleep(0)


async def test_logging_handler_with_async_client_schedules_publish(mock_router):
    route = mock_router.post("/event").mock(return_value=_ack())
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as client:
        logger = logging.getLogger("axonpush.test.async_handler")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(
            AxonPushLoggingHandler(client=client, channel_id=5, service_name="async")
        )
        try:
            logger.error("from async path")
            await _drain_loop()
        finally:
            logger.handlers.clear()

    assert route.call_count == 1, (
        "expected the async-client logging handler to schedule and complete "
        "exactly one publish, got "
        f"{route.call_count}"
    )
    body = json.loads(route.calls.last.request.content)
    assert body["payload"]["body"] == "from async path"
    assert body["payload"]["severityText"] == "ERROR"


async def test_loguru_sink_with_async_client_schedules_publish(mock_router):
    pytest.importorskip("loguru")
    from loguru import logger as loguru_logger

    from axonpush.integrations.loguru import create_axonpush_loguru_sink

    route = mock_router.post("/event").mock(return_value=_ack())
    loguru_logger.remove()
    try:
        async with AsyncAxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
        ) as client:
            loguru_logger.add(
                create_axonpush_loguru_sink(client=client, channel_id=5),
                serialize=True,
            )
            loguru_logger.error("loguru async")
            await _drain_loop()
    finally:
        loguru_logger.remove()

    assert route.call_count == 1
    body = json.loads(route.calls.last.request.content)
    assert body["payload"]["body"] == "loguru async"


async def test_structlog_processor_with_async_client_schedules_publish(mock_router):
    pytest.importorskip("structlog")
    import structlog

    from axonpush.integrations.structlog import axonpush_structlog_processor

    route = mock_router.post("/event").mock(return_value=_ack())
    structlog.reset_defaults()
    try:
        async with AsyncAxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
        ) as client:
            forwarder = axonpush_structlog_processor(client=client, channel_id=5)
            forwarder(None, "error", {"event": "structlog async"})
            await _drain_loop()
    finally:
        structlog.reset_defaults()

    assert route.call_count == 1
    body = json.loads(route.calls.last.request.content)
    assert body["payload"]["body"] == "structlog async"


async def test_print_capture_with_async_client_schedules_publish(mock_router):
    import sys

    from axonpush.integrations.print_capture import setup_print_capture

    route = mock_router.post("/event").mock(return_value=_ack())
    orig_out, orig_err = sys.stdout, sys.stderr
    try:
        async with AsyncAxonPush(
            api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
        ) as client:
            handle = setup_print_capture(client, channel_id=5)
            try:
                print("print async")
                await _drain_loop()
            finally:
                handle.unpatch()
    finally:
        sys.stdout, sys.stderr = orig_out, orig_err

    assert route.call_count == 1
    body = json.loads(route.calls.last.request.content)
    assert body["payload"]["body"] == "print async"


async def test_otel_exporter_with_async_client_schedules_publish(mock_router):
    pytest.importorskip("opentelemetry.sdk.trace")
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    from axonpush.integrations.otel import AxonPushSpanExporter

    route = mock_router.post("/event").mock(return_value=_ack())
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as client:
        exporter = AxonPushSpanExporter(client=client, channel_id=5)
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer(__name__)
        with tracer.start_as_current_span("async-span"):
            pass
        await _drain_loop()
        provider.shutdown()

    assert route.call_count == 1
    body = json.loads(route.calls.last.request.content)
    assert body["identifier"] == "async-span"


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
async def test_no_running_loop_swallows_runtime_error(mock_router):
    """When the user uses an AsyncAxonPush from a thread with no running loop,
    the handler should NOT crash. The integrations all wrap the
    ``loop.create_task`` call in ``except RuntimeError: pass`` for this case.

    We simulate "no running loop" by calling the handler synchronously from a
    worker thread (where ``asyncio.get_running_loop()`` raises RuntimeError).
    The publish coroutine is dropped silently — no event reaches respx, but
    the user's code keeps running. This pins the fail-quiet contract.
    """
    import threading

    mock_router.post("/event").mock(return_value=_ack())
    async with AsyncAxonPush(
        api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL
    ) as client:
        logger = logging.getLogger("axonpush.test.async_no_loop")
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(
            AxonPushLoggingHandler(client=client, channel_id=5)
        )

        crashed: list[BaseException] = []

        def worker():
            try:
                logger.error("from worker thread")
            except BaseException as exc:  # pragma: no cover
                crashed.append(exc)

        t = threading.Thread(target=worker)
        t.start()
        t.join(timeout=2)

        try:
            assert not crashed, f"handler raised in thread: {crashed[0]!r}"
        finally:
            logger.handlers.clear()
