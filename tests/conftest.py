import uuid

import pytest

from axonpush import AxonPush, AsyncAxonPush

BASE_URL = "http://localhost:3000"
API_KEY = "ak_37da12ee64d259dc2f214211095d01289d6ea9c3a45d22c2f59c51209475965f"
TENANT_ID = "1"
EXISTING_APP_ID = 1


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
