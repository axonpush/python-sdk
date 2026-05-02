import uuid

import pytest

from axonpush.exceptions import NotFoundError
from axonpush.models import Channel

pytestmark = pytest.mark.e2e


class TestChannels:
    def test_create_channel(self, client, backend):
        name = f"test-ch-{uuid.uuid4().hex[:8]}"
        ch = client.channels.create(name, backend.app_id)
        assert isinstance(ch, Channel)
        assert ch.name == name
        assert ch.id is not None
        client.channels.delete(ch.id)

    def test_get_channel(self, client, channel):
        fetched = client.channels.get(channel.id)
        assert fetched.id == channel.id
        assert fetched.name == channel.name

    def test_delete_channel(self, client, backend):
        name = f"test-ch-{uuid.uuid4().hex[:8]}"
        ch = client.channels.create(name, backend.app_id)
        client.channels.delete(ch.id)
        with pytest.raises((NotFoundError, Exception)):
            client.channels.get(ch.id)
