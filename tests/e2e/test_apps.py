import pytest

from axonpush.models.apps import App

pytestmark = pytest.mark.e2e


class TestAppsResource:
    def test_get_app(self, client, backend):
        app = client.apps.get(backend.app_id)
        assert isinstance(app, App)
        assert app.id == backend.app_id
        assert app.name is not None

    def test_get_app_has_channels(self, client, backend):
        app = client.apps.get(backend.app_id)
        assert isinstance(app.channels, list)
