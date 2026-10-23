"""Konstanten für DB Pendler."""

from __future__ import annotations

DOMAIN = "db_pendler"
VERSION = "1.0.1"

DEFAULT_BASE_URL = "https://api.transitous.org"
USER_AGENT = f"HomeAssistant-DBPendler/{VERSION} (+https://github.com/hacs/integration)"
ATTRIBUTION = "Daten: Transitous (transitous.org) / DELFI, inkl. DB-Echtzeitdaten"

CONF_FROM_ID = "from_id"
CONF_FROM_NAME = "from_name"
CONF_TO_ID = "to_id"
CONF_TO_NAME = "to_name"
CONF_FROM_QUERY = "from_query"
CONF_TO_QUERY = "to_query"

CONF_OFFSET = "offset"
CONF_RESULTS = "results"
CONF_PRODUCTS = "products"
CONF_MAX_TRANSFERS = "max_transfers"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USE_WINDOW = "use_active_window"
CONF_WINDOW_START = "active_start"
CONF_WINDOW_END = "active_end"
CONF_BASE_URL = "base_url"

DEFAULT_OFFSET = 0
DEFAULT_RESULTS = 5
DEFAULT_PRODUCTS = "all"
DEFAULT_MAX_TRANSFERS = 3
DEFAULT_SCAN_INTERVAL = 3  # Minuten
DEFAULT_USE_WINDOW = False
DEFAULT_WINDOW_START = "05:00:00"
DEFAULT_WINDOW_END = "10:00:00"
IDLE_SCAN_INTERVAL = 30  # Minuten, außerhalb des aktiven Zeitfensters

# Verkehrsmittel-Filter -> MOTIS transitModes
PRODUCTS = {
    "all": "TRANSIT",
    "regional": "REGIONAL_FAST_RAIL,REGIONAL_RAIL,SUBURBAN,SUBWAY,TRAM,BUS,FERRY",
    "rail": "RAIL",
    "regional_rail": "REGIONAL_FAST_RAIL,REGIONAL_RAIL,SUBURBAN",
}

FRONTEND_URL = "/db_pendler/db-pendler-card.js"
