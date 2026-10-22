"""Client für die Transitous/MOTIS-API (Fahrplan inkl. DB-Echtzeitdaten)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import aiohttp

from .const import USER_AGENT

NON_TRANSIT_MODES = {"WALK", "BIKE", "CAR", "RENTAL", "CAR_PARKING", "CAR_DROPOFF", "FLEX", "ODM"}


class PendlerApiError(Exception):
    """Fehler beim Abruf der Fahrplandaten."""


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _delay_minutes(actual: datetime | None, planned: datetime | None) -> int:
    if actual is None or planned is None:
        return 0
    return round((actual - planned).total_seconds() / 60)


class PendlerApi:
    """Dünner async Wrapper um die MOTIS-Endpunkte geocode und plan."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: dict[str, Any]) -> Any:
        try:
            async with asyncio.timeout(30):
                resp = await self._session.get(
                    f"{self._base_url}{path}",
                    params=params,
                    headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                )
                if resp.status != 200:
                    text = await resp.text()
                    raise PendlerApiError(f"HTTP {resp.status}: {text[:200]}")
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise PendlerApiError(str(err)) from err

    async def search_stops(self, text: str) -> list[dict[str, str]]:
        """Haltestellen per Name suchen."""
        data = await self._get(
            "/api/v1/geocode", {"text": text, "type": "STOP", "language": "de"}
        )
        stops: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in data:
            area = next(
                (a["name"] for a in item.get("areas", []) if a.get("default")), ""
            )
            label = item["name"] if not area or area in item["name"] else f"{item['name']} ({area})"
            if label in seen:
                continue
            seen.add(label)
            stops.append({"id": item["id"], "name": item["name"], "label": label})
        return stops[:10]

    async def get_connections(
        self,
        from_id: str,
        to_id: str,
        departure: datetime,
        results: int,
        transit_modes: str,
        max_transfers: int,
    ) -> list[dict[str, Any]]:
        """Verbindungen ab einem Zeitpunkt abfragen und vereinfacht zurückgeben."""
        data = await self._get(
            "/api/v5/plan",
            {
                "fromPlace": from_id,
                "toPlace": to_id,
                "time": departure.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "numItineraries": results,
                "transitModes": transit_modes,
                "maxTransfers": max_transfers,
                "language": "de",
            },
        )
        connections = [
            conn
            for it in data.get("itineraries", [])
            if (conn := _parse_itinerary(it)) is not None
        ]
        return _dedupe(connections)


def _line_name(leg: dict[str, Any]) -> str:
    """„RB67“ statt „RB67 (86585)“, aber „ICE 1013“ statt nur der Liniennummer „18“."""
    short = leg.get("routeShortName") or ""
    if any(ch.isalpha() for ch in short):
        return short
    return leg.get("displayName") or short or leg.get("mode", "?")


def _parse_itinerary(itinerary: dict[str, Any]) -> dict[str, Any] | None:
    legs = [l for l in itinerary.get("legs", []) if l.get("mode") not in NON_TRANSIT_MODES]
    if not legs:
        return None
    first, last = legs[0], legs[-1]

    dep = _parse_time(first.get("startTime"))
    dep_planned = _parse_time(first.get("scheduledStartTime"))
    arr = _parse_time(last.get("endTime"))
    arr_planned = _parse_time(last.get("scheduledEndTime"))

    parsed_legs = []
    alerts: list[str] = []
    for leg in legs:
        leg_dep = _parse_time(leg.get("startTime"))
        leg_dep_planned = _parse_time(leg.get("scheduledStartTime"))
        leg_arr = _parse_time(leg.get("endTime"))
        leg_arr_planned = _parse_time(leg.get("scheduledEndTime"))
        frm, to = leg.get("from", {}), leg.get("to", {})
        parsed_legs.append(
            {
                "line": _line_name(leg),
                "name": leg.get("displayName") or leg.get("routeShortName"),
                "mode": leg.get("mode"),
                "direction": leg.get("headsign"),
                "from": frm.get("name"),
                "to": to.get("name"),
                "departure": leg_dep.isoformat() if leg_dep else None,
                "departure_planned": leg_dep_planned.isoformat() if leg_dep_planned else None,
                "departure_delay": _delay_minutes(leg_dep, leg_dep_planned),
                "arrival": leg_arr.isoformat() if leg_arr else None,
                "arrival_planned": leg_arr_planned.isoformat() if leg_arr_planned else None,
                "arrival_delay": _delay_minutes(leg_arr, leg_arr_planned),
                "platform": frm.get("track") or frm.get("scheduledTrack"),
                "platform_planned": frm.get("scheduledTrack"),
                "arrival_platform": to.get("track") or to.get("scheduledTrack"),
                "cancelled": bool(leg.get("cancelled") or frm.get("cancelled") or to.get("cancelled")),
                "realtime": bool(leg.get("realTime")),
                "trip_id": leg.get("tripId"),
            }
        )
        for alert in leg.get("alerts") or []:
            text = alert.get("headerText") or alert.get("descriptionText")
            if text and text not in alerts:
                alerts.append(text)

    first_leg = parsed_legs[0]
    return {
        "departure": first_leg["departure"],
        "departure_planned": first_leg["departure_planned"],
        "departure_delay": first_leg["departure_delay"],
        "arrival": arr.isoformat() if arr else None,
        "arrival_planned": arr_planned.isoformat() if arr_planned else None,
        "arrival_delay": _delay_minutes(arr, arr_planned),
        "duration": round((arr - dep).total_seconds() / 60) if arr and dep else None,
        "transfers": len(legs) - 1,
        "lines": [l["line"] for l in parsed_legs],
        "platform": first_leg["platform"],
        "platform_planned": first_leg["platform_planned"],
        "platform_changed": bool(
            first_leg["platform_planned"]
            and first_leg["platform"] != first_leg["platform_planned"]
        ),
        "cancelled": any(l["cancelled"] for l in parsed_legs),
        "realtime": any(l["realtime"] for l in parsed_legs),
        "alerts": alerts,
        "legs": parsed_legs,
    }


def _dedupe(connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gleicher erster Zug → nur die Variante mit frühester Ankunft behalten."""
    best: dict[tuple, dict[str, Any]] = {}
    for conn in connections:
        key = (conn["legs"][0]["trip_id"], conn["departure"])
        cur = best.get(key)
        if cur is None or (conn["arrival"], conn["transfers"]) < (cur["arrival"], cur["transfers"]):
            best[key] = conn
    return sorted(best.values(), key=lambda c: c["departure"] or "")
