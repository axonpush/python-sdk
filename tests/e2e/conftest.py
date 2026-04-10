"""Fixtures that require a live easy-push backend.

These fixtures live under ``tests/e2e/`` so that the unit suite never
accidentally pulls them in (and never tries to hit a real backend on
``client.apps.get(...)``).

Run via ``pytest -m e2e`` (or ``scripts/test-e2e.sh``).
"""
from __future__ import annotations

import uuid

import pytest

from tests.conftest import EXISTING_APP_ID


@pytest.fixture()
def app(client):
    return client.apps.get(EXISTING_APP_ID)


@pytest.fixture()
def channel(client, app):
    name = f"test-channel-{uuid.uuid4().hex[:8]}"
    created = client.channels.create(name, app.id)
    yield created
    try:
        client.channels.delete(created.id)
    except Exception:
        pass
