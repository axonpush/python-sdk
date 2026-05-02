"""Shared pytest configuration for the axonpush test suite.

The test suite is split into two tiers:

* ``tests/unit/`` — fast, mocked with ``respx``, no backend required.
  Run on every push/PR and as the gate before publishing to PyPI.

* ``tests/e2e/`` — end-to-end tests against a live easy-push backend.
  Marked ``@pytest.mark.e2e``; opt in with ``pytest -m e2e`` (or via
  ``scripts/test-e2e.sh`` which boots easy-push first).

Backend connection details for e2e tests are read from environment
variables so they work both on a developer laptop and in CI:

    AXONPUSH_BASE_URL    default: http://localhost:3000
    AXONPUSH_API_KEY     default: ak_test
    AXONPUSH_TENANT_ID   default: 1
    AXONPUSH_APP_ID      default: 1
"""

from __future__ import annotations

import os

import pytest
import respx

from axonpush import AsyncAxonPush, AxonPush
from axonpush import _tracing

BASE_URL = os.getenv("AXONPUSH_BASE_URL", "http://localhost:3000")
API_KEY = os.getenv("AXONPUSH_API_KEY", "ak_test")
TENANT_ID = os.getenv("AXONPUSH_TENANT_ID", "1")
EXISTING_APP_ID = os.getenv("AXONPUSH_APP_ID", "1")


@pytest.fixture(autouse=True)
def _reset_trace_context():
    """Prevent ``axonpush._tracing._current_trace`` from leaking between tests.

    The trace context is a process-wide ``ContextVar``. Without a reset, the
    first test that calls ``get_or_create_trace()`` plants a trace_id that
    every subsequent test inherits — making "auto-generated trace_id" assertions
    silently test the leftover value instead of fresh generation.
    """
    token = _tracing._current_trace.set(None)
    try:
        yield
    finally:
        _tracing._current_trace.reset(token)


@pytest.fixture()
def mock_router():
    """A respx router scoped to the configured BASE_URL.

    Use in unit tests to intercept HTTP traffic from the SDK without a real
    backend. ``assert_all_called=False`` so tests can register routes that
    aren't necessarily exercised on every code path.
    """
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture()
def client():
    c = AxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL)
    yield c
    c.close()


@pytest.fixture()
async def async_client():
    c = AsyncAxonPush(api_key=API_KEY, tenant_id=TENANT_ID, base_url=BASE_URL)
    yield c
    await c.close()
