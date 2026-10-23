"""DataUpdateCoordinator für DB Pendler."""

from __future__ import annotations

from datetime import time, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PendlerApi, PendlerApiError
from .const import (
    CONF_BASE_URL,
    CONF_FROM_ID,
    CONF_FROM_NAME,
    CONF_MAX_TRANSFERS,
    CONF_OFFSET,
    CONF_PRODUCTS,
    CONF_RESULTS,
    CONF_SCAN_INTERVAL,
    CONF_TO_ID,
    CONF_TO_NAME,
    CONF_USE_WINDOW,
    CONF_WINDOW_END,
    CONF_WINDOW_START,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TRANSFERS,
    DEFAULT_OFFSET,
    DEFAULT_PRODUCTS,
    DEFAULT_RESULTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USE_WINDOW,
    DEFAULT_WINDOW_END,
    DEFAULT_WINDOW_START,
    DOMAIN,
    IDLE_SCAN_INTERVAL,
    PRODUCTS,
)

_LOGGER = logging.getLogger(__name__)


class PendlerCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Holt regelmäßig die nächsten Verbindungen."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.opts = {**entry.data, **entry.options}
        self._active_interval = timedelta(
            minutes=self.opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.title}",
            update_interval=self._active_interval,
        )
        self.api = PendlerApi(
            async_get_clientsession(hass),
            self.opts.get(CONF_BASE_URL) or DEFAULT_BASE_URL,
        )

    def _in_active_window(self) -> bool:
        if not self.opts.get(CONF_USE_WINDOW, DEFAULT_USE_WINDOW):
            return True
        start = time.fromisoformat(self.opts.get(CONF_WINDOW_START, DEFAULT_WINDOW_START))
        end = time.fromisoformat(self.opts.get(CONF_WINDOW_END, DEFAULT_WINDOW_END))
        now = dt_util.now().time()
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end  # Fenster über Mitternacht

    async def _async_update_data(self) -> list[dict[str, Any]]:
        active = self._in_active_window()
        self.update_interval = (
            self._active_interval if active else timedelta(minutes=IDLE_SCAN_INTERVAL)
        )

        start = dt_util.utcnow() + timedelta(
            minutes=self.opts.get(CONF_OFFSET, DEFAULT_OFFSET)
        )
        try:
            connections = await self.api.get_connections(
                from_id=self.opts[CONF_FROM_ID],
                to_id=self.opts[CONF_TO_ID],
                departure=start,
                results=int(self.opts.get(CONF_RESULTS, DEFAULT_RESULTS)),
                transit_modes=PRODUCTS[self.opts.get(CONF_PRODUCTS, DEFAULT_PRODUCTS)],
                max_transfers=int(self.opts.get(CONF_MAX_TRANSFERS, DEFAULT_MAX_TRANSFERS)),
            )
        except PendlerApiError as err:
            raise UpdateFailed(f"Fahrplan konnte nicht geladen werden: {err}") from err

        # Die API liefert Namen teils übersetzt („Munich“) – Start/Ziel wie eingerichtet anzeigen
        for conn in connections:
            conn["legs"][0]["from"] = self.opts.get(CONF_FROM_NAME) or conn["legs"][0]["from"]
            conn["legs"][-1]["to"] = self.opts.get(CONF_TO_NAME) or conn["legs"][-1]["to"]

        return connections[: int(self.opts.get(CONF_RESULTS, DEFAULT_RESULTS))]
