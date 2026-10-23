"""DB Pendler – nächste Bahnverbindungen für den Arbeitsweg."""

from __future__ import annotations

import hashlib
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, FRONTEND_URL
from .coordinator import PendlerCoordinator

PLATFORMS = [Platform.SENSOR]
CARD_PATH = Path(__file__).parent / "frontend" / "db-pendler-card.js"
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type PendlerConfigEntry = ConfigEntry[PendlerCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Lovelace-Karte automatisch ausliefern und im Frontend laden."""
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_URL,
                str(CARD_PATH),
                cache_headers=False,
            )
        ]
    )
    # Hash des Dateiinhalts als Cache-Buster: jede Änderung an der Karte erzwingt ein Neuladen im Browser
    card_hash = await hass.async_add_executor_job(
        lambda: hashlib.sha256(CARD_PATH.read_bytes()).hexdigest()[:8]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL}?v={card_hash}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PendlerConfigEntry) -> bool:
    coordinator = PendlerCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PendlerConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: PendlerConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
