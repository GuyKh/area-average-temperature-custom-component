"""Sensor platform for area_average_temperature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers import area_registry, entity_registry

from .const import DOMAIN
from .entity import AreaAverageTemperatureEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AreaAverageTemperatureCoordinator
    from .data import AreaAverageTemperatureConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AreaAverageTemperatureConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    entities = [
        AreaAverageTemperatureSensor(coordinator=coordinator, area_key=area_key)
        for area_key in coordinator.area_sensors
    ]
    async_add_entities(entities)

    # Ensure entities are assigned to their areas
    entity_reg = entity_registry.async_get(hass)
    area_reg = area_registry.async_get(hass)
    for entity in entities:
        area = None
        for a in area_reg.areas.values():
            if a.name == entity.area_name:
                area = a
                break
        if area:
            entity_reg.async_update_entity(entity.entity_id, area_id=area.id)

    # Listen for config entry updates to add/remove sensors
    async def async_update_sensors() -> None:
        """Update sensors when area configuration changes."""
        current_areas = set(coordinator.area_sensors.keys())
        existing_areas = set()

        # Find existing sensors
        for entity in hass.data.get("entity_registry", {}).entities.values():
            if entity.config_entry_id == entry.entry_id and entity.domain == "sensor":
                # Extract area key from unique_id
                unique_id_parts = entity.unique_id.split("_")
                if len(unique_id_parts) > 1:
                    area_key = "_".join(unique_id_parts[1:])
                    existing_areas.add(area_key)

        # Add new sensors
        new_areas = current_areas - existing_areas
        if new_areas:
            new_entities = [
                AreaAverageTemperatureSensor(coordinator, area_key)
                for area_key in new_areas
            ]
            async_add_entities(new_entities)

        # Remove old sensors (this would require removing entities, but HA doesn't support this easily)
        # For now, we'll just update the coordinator data

    entry.async_on_unload(coordinator.async_add_listener(async_update_sensors))


class AreaAverageTemperatureSensor(AreaAverageTemperatureEntity, SensorEntity):
    """Area Average Temperature Sensor class."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @staticmethod
    def _normalize_area_key(area_key: str) -> str:
        """Normalize area key by removing common unwanted prefixes."""
        key = area_key.lower()
        prefixes_to_remove = ["area", "average", "temperature", "sensor"]
        for prefix in prefixes_to_remove:
            key = key.replace(prefix, "")
        key = key.strip("_").replace("__", "_").strip("_")
        return key or area_key

    def __init__(
        self,
        coordinator: AreaAverageTemperatureCoordinator,
        area_key: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.original_area_key = area_key
        normalized_key = self._normalize_area_key(area_key)
        self.area_key = normalized_key
        self.area_name = normalized_key.replace("_", " ").title()
        self._attr_translation_key = "area_average_temperature"
        self._attr_translation_placeholders = {"area_name": self.area_name}
        self._attr_unique_id = f"{DOMAIN}_{normalized_key}"
        self._attr_entity_id = f"sensor.{normalized_key}_average_temperature"
        self._attr_suggested_area = self.area_name

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.get(self.original_area_key)
