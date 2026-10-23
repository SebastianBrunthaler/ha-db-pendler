"""Sensoren für DB Pendler."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PendlerConfigEntry
from .const import ATTRIBUTION, CONF_FROM_NAME, CONF_TO_NAME, DOMAIN
from .coordinator import PendlerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PendlerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [NextDepartureSensor(coordinator), DelaySensor(coordinator)]
    )


class PendlerEntity(CoordinatorEntity[PendlerCoordinator]):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: PendlerCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="DB Pendler",
            model="Verbindung",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _next(self) -> dict[str, Any] | None:
        """Nächste nicht ausgefallene Verbindung (sonst die erste)."""
        data = self.coordinator.data or []
        return next((c for c in data if not c["cancelled"]), data[0] if data else None)


class NextDepartureSensor(PendlerEntity, SensorEntity):
    """Abfahrtszeit der nächsten Verbindung; alle Verbindungen als Attribut."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:train"
    _unrecorded_attributes = frozenset({"connections"})

    def __init__(self, coordinator: PendlerCoordinator) -> None:
        super().__init__(coordinator, "next_departure")

    @property
    def native_value(self) -> datetime | None:
        conn = self._next
        if conn and conn["departure"]:
            return datetime.fromisoformat(conn["departure"])
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        opts = self.coordinator.opts
        conn = self._next or {}
        return {
            "db_pendler": True,
            "from_station": opts.get(CONF_FROM_NAME),
            "to_station": opts.get(CONF_TO_NAME),
            "lines": conn.get("lines"),
            "platform": conn.get("platform"),
            "departure_planned": conn.get("departure_planned"),
            "departure_delay": conn.get("departure_delay"),
            "arrival": conn.get("arrival"),
            "arrival_delay": conn.get("arrival_delay"),
            "duration": conn.get("duration"),
            "transfers": conn.get("transfers"),
            "connections": self.coordinator.data or [],
        }


class DelaySensor(PendlerEntity, SensorEntity):
    """Verspätung der nächsten Verbindung in Minuten – praktisch für Automationen."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: PendlerCoordinator) -> None:
        super().__init__(coordinator, "delay")

    @property
    def native_value(self) -> int | None:
        conn = self._next
        return conn["departure_delay"] if conn else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        conn = self._next or {}
        return {
            "cancelled_connections": sum(
                1 for c in self.coordinator.data or [] if c["cancelled"]
            ),
            "line": " → ".join(conn.get("lines") or []),
        }
