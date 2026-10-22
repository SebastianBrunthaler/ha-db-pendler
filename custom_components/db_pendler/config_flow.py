"""Config- und Options-Flow für DB Pendler."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TimeSelector,
)

from .api import PendlerApi, PendlerApiError
from .const import (
    CONF_BASE_URL,
    CONF_FROM_ID,
    CONF_FROM_NAME,
    CONF_FROM_QUERY,
    CONF_MAX_TRANSFERS,
    CONF_OFFSET,
    CONF_PRODUCTS,
    CONF_RESULTS,
    CONF_SCAN_INTERVAL,
    CONF_TO_ID,
    CONF_TO_NAME,
    CONF_TO_QUERY,
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
    PRODUCTS,
)


def _number(min_: int, max_: int, unit: str | None = None) -> NumberSelector:
    config = NumberSelectorConfig(min=min_, max=max_, step=1, mode=NumberSelectorMode.BOX)
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


def options_schema(d: dict[str, Any]) -> dict:
    """Gemeinsames Schema für Ersteinrichtung und Optionen."""
    return {
        vol.Required(CONF_OFFSET, default=d.get(CONF_OFFSET, DEFAULT_OFFSET)): _number(0, 120, "min"),
        vol.Required(CONF_RESULTS, default=d.get(CONF_RESULTS, DEFAULT_RESULTS)): _number(1, 10),
        vol.Required(CONF_PRODUCTS, default=d.get(CONF_PRODUCTS, DEFAULT_PRODUCTS)): SelectSelector(
            SelectSelectorConfig(options=list(PRODUCTS), translation_key=CONF_PRODUCTS)
        ),
        vol.Required(
            CONF_MAX_TRANSFERS, default=d.get(CONF_MAX_TRANSFERS, DEFAULT_MAX_TRANSFERS)
        ): _number(0, 6),
        vol.Required(
            CONF_SCAN_INTERVAL, default=d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ): _number(1, 60, "min"),
        vol.Required(CONF_USE_WINDOW, default=d.get(CONF_USE_WINDOW, DEFAULT_USE_WINDOW)): BooleanSelector(),
        vol.Required(
            CONF_WINDOW_START, default=d.get(CONF_WINDOW_START, DEFAULT_WINDOW_START)
        ): TimeSelector(),
        vol.Required(
            CONF_WINDOW_END, default=d.get(CONF_WINDOW_END, DEFAULT_WINDOW_END)
        ): TimeSelector(),
    }


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    """NumberSelector liefert floats – für Minuten/Anzahlen ints speichern."""
    out = dict(user_input)
    for key in (CONF_OFFSET, CONF_RESULTS, CONF_MAX_TRANSFERS, CONF_SCAN_INTERVAL):
        if key in out:
            out[key] = int(out[key])
    return out


class PendlerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._from_stops: list[dict[str, str]] = []
        self._to_stops: list[dict[str, str]] = []
        self._base_url = DEFAULT_BASE_URL

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schritt 1: Start und Ziel als Text eingeben."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._base_url = user_input.get(CONF_BASE_URL) or DEFAULT_BASE_URL
            api = PendlerApi(async_get_clientsession(self.hass), self._base_url)
            try:
                self._from_stops = await api.search_stops(user_input[CONF_FROM_QUERY])
                self._to_stops = await api.search_stops(user_input[CONF_TO_QUERY])
            except PendlerApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self._from_stops:
                    errors[CONF_FROM_QUERY] = "no_stops"
                if not self._to_stops:
                    errors[CONF_TO_QUERY] = "no_stops"
                if not errors:
                    return await self.async_step_stations()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_FROM_QUERY): TextSelector(),
                        vol.Required(CONF_TO_QUERY): TextSelector(),
                        vol.Optional(CONF_BASE_URL): TextSelector(),
                    }
                ),
                user_input or {CONF_BASE_URL: DEFAULT_BASE_URL},
            ),
            errors=errors,
        )

    async def async_step_stations(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Schritt 2: passende Haltestellen auswählen + Optionen."""
        if user_input is not None:
            frm = next(s for s in self._from_stops if s["id"] == user_input[CONF_FROM_ID])
            to = next(s for s in self._to_stops if s["id"] == user_input[CONF_TO_ID])
            await self.async_set_unique_id(f"{frm['id']}__{to['id']}")
            self._abort_if_unique_id_configured()
            data = {
                CONF_FROM_ID: frm["id"],
                CONF_FROM_NAME: frm["name"],
                CONF_TO_ID: to["id"],
                CONF_TO_NAME: to["name"],
                CONF_BASE_URL: self._base_url,
            }
            options = _clean(
                {k: v for k, v in user_input.items() if k not in (CONF_FROM_ID, CONF_TO_ID)}
            )
            return self.async_create_entry(
                title=f"{frm['name']} → {to['name']}", data=data, options=options
            )

        def stop_select(stops: list[dict[str, str]]) -> SelectSelector:
            return SelectSelector(
                SelectSelectorConfig(
                    options=[SelectOptionDict(value=s["id"], label=s["label"]) for s in stops],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="stations",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_FROM_ID, default=self._from_stops[0]["id"]): stop_select(self._from_stops),
                    vol.Required(CONF_TO_ID, default=self._to_stops[0]["id"]): stop_select(self._to_stops),
                    **options_schema({}),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PendlerOptionsFlow()


class PendlerOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options_schema(dict(self.config_entry.options))),
        )
