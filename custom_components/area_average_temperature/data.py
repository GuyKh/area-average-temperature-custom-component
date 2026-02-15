"""Custom types for area_average_temperature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .coordinator import AreaAverageTemperatureCoordinator


type AreaAverageTemperatureConfigEntry = ConfigEntry[AreaAverageTemperatureData]


@dataclass
class AreaAverageTemperatureData:
    """Data for the Area Average Temperature integration."""

    coordinator: AreaAverageTemperatureCoordinator
    integration: Integration
