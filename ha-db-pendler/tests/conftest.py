from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def fake_frontend(tmp_path):
    """Das Paket hass_frontend ist in Testumgebungen nicht installiert – leeres Verzeichnis nutzen."""
    for sub in ("static", "frontend_latest", "frontend_es5", "static/icons"):
        (tmp_path / "hass_frontend" / sub).mkdir(parents=True, exist_ok=True)
    with patch(
        "homeassistant.components.frontend._frontend_root",
        return_value=tmp_path / "hass_frontend",
    ):
        yield
