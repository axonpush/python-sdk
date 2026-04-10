import uuid

import pytest

from axonpush.models.channels import Channel
from tests.conftest import EXISTING_APP_ID

pytestmark = pytest.mark.e2e


class TestChannelsResource:
    def test_create_channel(self, client):
        name = f"test-ch-{uuid.uuid4().hex[:8]}"
        ch = client.channels.create(name, EXISTING_APP_ID)
        assert isinstance(ch, Channel)
        assert ch.name == name
        assert ch.id is not None
        client.channels.delete(ch.id)

    def test_get_channel(self, client, channel):
        fetched = client.channels.get(channel.id)
        assert fetched.id == channel.id
        assert fetched.name == channel.name

    def test_delete_channel(self, client):
        name = f"test-ch-{uuid.uuid4().hex[:8]}"
        ch = client.channels.create(name, EXISTING_APP_ID)
        client.channels.delete(ch.id)
        from axonpush.exceptions import NotFoundError
        with pytest.raises((NotFoundError, Exception)):
            client.channels.get(ch.id)
