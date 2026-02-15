"""DataUpdateCoordinator for area_average_temperature."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

if TYPE_CHECKING:
    from .data import AreaAverageTemperatureConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class AreaAverageTemperatureCoordinator(DataUpdateCoordinator):
    """Class to manage fetching temperature data and calculating averages."""

    config_entry: AreaAverageTemperatureConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        logger,  # type: ignore[no-untyped-def]
        name: str,
        config_entry: AreaAverageTemperatureConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, logger, name=name, update_interval=None)
        self.config_entry = config_entry
        self._area_sensors: dict[str, list[str]] = config_entry.options.get(
            "areas", config_entry.data.get("areas", {})
        )
        self._unsubscribers: list[Any] = []

    async def async_config_entry_first_refresh(self) -> None:
        """Set up state change listeners after first refresh."""
        await super().async_config_entry_first_refresh()
        await self._setup_listeners()

    async def _setup_listeners(self) -> None:
        """Set up listeners for temperature sensor state changes."""
        # Clean up existing listeners
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()

        # Get all sensor IDs
        all_sensor_ids = []
        for sensors in self._area_sensors.values():
            all_sensor_ids.extend(sensors)

        if all_sensor_ids:
            # Set up listener for state changes
            self._unsubscribers.append(
                async_track_state_change_event(
                    self.hass,
                    all_sensor_ids,
                    self._handle_state_change,
                )
            )

    @callback
    async def _handle_state_change(self, event) -> None:  # type: ignore[no-untyped-def]
        """Handle state change events for temperature sensors."""
        await self.async_refresh()

    async def _async_update_data(self) -> dict[str, float]:
        """Update data by calculating average temperatures for each area."""
        area_averages = {}

        for area_name, sensor_ids in self._area_sensors.items():
            temperatures = []
            for sensor_id in sensor_ids:
                state = self.hass.states.get(sensor_id)
                if state and state.state not in [None, "unknown", "unavailable"]:
                    try:
                        temp = float(state.state)
                        temperatures.append(temp)
                    except (ValueError, TypeError):
                        continue

            if temperatures:
                area_averages[area_name] = sum(temperatures) / len(temperatures)

        return area_averages

    @property
    def area_sensors(self):
        """Get the current area sensors mapping."""
        return self._area_sensors

    def update_area_sensors(self, area_sensors) -> None:
        """Update the area to sensor mapping."""
        self._area_sensors = area_sensors
        # Re-setup listeners with new sensors
        self.hass.async_create_task(self._setup_listeners())
