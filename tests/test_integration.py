"""Tests für Config-Flow, Setup und Sensoren (API gemockt)."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util

from custom_components.db_pendler.api import _parse_itinerary
from custom_components.db_pendler.const import DOMAIN

STOPS_FROM = [{"id": "aug", "name": "Augsburg Hbf", "label": "Augsburg Hbf"}]
STOPS_TO = [{"id": "muc", "name": "München Hbf", "label": "München Hbf"}]


def _iso(minutes: int) -> str:
    return (dt_util.utcnow() + timedelta(minutes=minutes)).replace(microsecond=0).isoformat()


def _itinerary(dep: int, delay: int, cancelled: bool = False) -> dict:
    return {
        "transfers": 1,
        "legs": [
            {"mode": "WALK", "from": {"name": "A"}, "to": {"name": "B"}},
            {
                "mode": "REGIONAL_RAIL", "routeShortName": "RB67", "displayName": "RB67 (86585)",
                "headsign": "Donauwörth", "tripId": f"t{dep}", "realTime": True, "cancelled": cancelled,
                "startTime": _iso(dep + delay), "scheduledStartTime": _iso(dep),
                "endTime": _iso(dep + 10 + delay), "scheduledEndTime": _iso(dep + 10),
                "from": {"name": "Augsburg Hbf", "track": "7", "scheduledTrack": "4"},
                "to": {"name": "Augsburg-Oberhausen", "track": "1"},
                "alerts": [{"headerText": "Bauarbeiten"}],
            },
            {
                "mode": "REGIONAL_RAIL", "routeShortName": "RE70", "displayName": "RE70 (3895)",
                "tripId": f"u{dep}", "realTime": True,
                "startTime": _iso(dep + 15), "scheduledStartTime": _iso(dep + 15),
                "endTime": _iso(dep + 50), "scheduledEndTime": _iso(dep + 45),
                "from": {"name": "Augsburg-Oberhausen", "track": "2"},
                "to": {"name": "München Hbf", "track": "20"},
            },
        ],
    }


def test_parse_itinerary():
    conn = _parse_itinerary(_itinerary(10, 3))
    assert conn["lines"] == ["RB67", "RE70"]
    assert conn["departure_delay"] == 3
    assert conn["arrival_delay"] == 5
    assert conn["transfers"] == 1
    assert conn["platform"] == "7" and conn["platform_changed"] is True
    assert conn["duration"] == 47
    assert conn["alerts"] == ["Bauarbeiten"]


async def test_full_flow_and_sensors(hass: HomeAssistant) -> None:
    connections = [_parse_itinerary(_itinerary(5, 0, cancelled=True)), _parse_itinerary(_itinerary(20, 4))]

    with (
        patch("custom_components.db_pendler.config_flow.PendlerApi.search_stops",
              AsyncMock(side_effect=[STOPS_FROM, STOPS_TO])),
        patch("custom_components.db_pendler.coordinator.PendlerApi.get_connections",
              AsyncMock(return_value=connections)) as get_conns,
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"from_query": "Augsburg", "to_query": "München"}
        )
        assert result["step_id"] == "stations"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"from_id": "aug", "to_id": "muc", "offset": 5.0, "results": 4.0, "products": "regional",
             "max_transfers": 2.0, "scan_interval": 3.0, "use_active_window": False,
             "active_start": "05:00:00", "active_end": "10:00:00"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "Augsburg Hbf → München Hbf"
        assert result["options"]["results"] == 4
        await hass.async_block_till_done()

        kwargs = get_conns.call_args.kwargs
        assert kwargs["from_id"] == "aug" and kwargs["max_transfers"] == 2
        assert "REGIONAL_RAIL" in kwargs["transit_modes"] and "HIGHSPEED" not in kwargs["transit_modes"]

    states = {s.entity_id: s for s in hass.states.async_all("sensor")}
    print(sorted(states))
    nxt = next(s for eid, s in states.items() if eid.endswith("next_departure"))
    delay = next(s for eid, s in states.items() if eid.endswith("delay"))
    # ausgefallene erste Verbindung wird übersprungen
    assert nxt.state == connections[1]["departure"]
    assert nxt.attributes["from_station"] == "Augsburg Hbf"
    assert len(nxt.attributes["connections"]) == 2
    assert nxt.attributes["db_pendler"] is True
    assert delay.state == "4"
    assert delay.attributes["cancelled_connections"] == 1

    # Options-Flow
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    with patch("custom_components.db_pendler.coordinator.PendlerApi.get_connections",
               AsyncMock(return_value=connections)):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            {"offset": 10, "results": 3, "products": "all", "max_transfers": 3, "scan_interval": 5,
             "use_active_window": True, "active_start": "05:30:00", "active_end": "09:00:00"},
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
    assert entry.options["offset"] == 10


async def test_card_js_is_served(hass: HomeAssistant, hass_client) -> None:
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_client()
    resp = await client.get("/db_pendler/db-pendler-card.js")
    assert resp.status == 200
    assert "db-pendler-card" in await resp.text()

    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL

    urls = hass.data[DATA_EXTRA_MODULE_URL].urls
    assert any(u.startswith("/db_pendler/db-pendler-card.js?v=") and len(u.split("=")[1]) == 8 for u in urls)
