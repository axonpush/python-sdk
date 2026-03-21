from axonpush.models.apps import App
from tests.conftest import EXISTING_APP_ID


class TestAppsResource:
    def test_get_app(self, client):
        app = client.apps.get(EXISTING_APP_ID)
        assert isinstance(app, App)
        assert app.id == EXISTING_APP_ID
        assert app.name is not None

    def test_get_app_has_channels(self, client):
        app = client.apps.get(EXISTING_APP_ID)
        assert isinstance(app.channels, list)
