"""
Custom integration to integrate area average temperature sensors with Home Assistant.

For more details about this integration, please refer to
https://github.com/guykh/area-average-temperature-custom-component
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN, LOGGER
from .coordinator import AreaAverageTemperatureCoordinator
from .data import AreaAverageTemperatureData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import AreaAverageTemperatureConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: AreaAverageTemperatureConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = AreaAverageTemperatureCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        config_entry=entry,
    )
    entry.runtime_data = AreaAverageTemperatureData(
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Listen for options updates
    async def async_options_updated(
        hass: HomeAssistant,
        config_entry: AreaAverageTemperatureConfigEntry,
    ) -> None:
        """Handle options update."""
        coordinator = entry.runtime_data.coordinator
        areas = config_entry.options.get("areas", config_entry.data.get("areas", {}))
        coordinator.update_area_sensors(areas)
        await coordinator.async_refresh()

    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AreaAverageTemperatureConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AreaAverageTemperatureConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
