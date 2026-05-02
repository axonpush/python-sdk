import pytest

from axonpush.models import App

pytestmark = pytest.mark.e2e


class TestApps:
    def test_get_app(self, client, backend):
        app = client.apps.get(backend.app_id)
        assert isinstance(app, App)
        assert app.id == backend.app_id
        assert app.name is not None

    def test_get_app_has_channels(self, client, backend):
        app = client.apps.get(backend.app_id)
        assert isinstance(app.channels, list)

    def test_list_apps_includes_bootstrapped(self, client, backend):
        apps = client.apps.list()
        assert isinstance(apps, list)
        assert backend.app_id in [a.id for a in apps]
