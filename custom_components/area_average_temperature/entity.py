"""AreaAverageTemperatureEntity class."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AreaAverageTemperatureCoordinator


class AreaAverageTemperatureEntity(
    CoordinatorEntity[AreaAverageTemperatureCoordinator]
):
    """AreaAverageTemperatureEntity class."""

    def __init__(self, coordinator: AreaAverageTemperatureCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
