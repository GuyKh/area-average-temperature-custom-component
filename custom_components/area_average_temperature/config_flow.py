"""Adds config flow for Area Average Temperature."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.area_registry import async_get as async_get_area_registry
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import DOMAIN


class AreaAverageTemperatureFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Area Average Temperature."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._areas: dict[str, list[str]] = {}

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_select()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):  # type: ignore[no-untyped-def]
        """Get the options flow for this handler."""
        return AreaAverageTemperatureOptionsFlowHandler(config_entry)

    async def _get_sensors_by_area(self) -> dict[str, list[str]]:
        """Get temperature sensors grouped by area."""
        entity_registry = async_get_entity_registry(self.hass)
        area_registry = async_get_area_registry(self.hass)
        device_registry = async_get_device_registry(self.hass)

        sensors_by_area: dict[str, list[str]] = {}

        for entity_id, entity_entry in entity_registry.entities.items():
            if entity_entry.domain == "sensor":
                state = self.hass.states.get(entity_id)
                if (
                    state
                    and state.attributes.get("device_class")
                    == SensorDeviceClass.TEMPERATURE.value
                ):
                    area_id = entity_entry.area_id
                    if not area_id and entity_entry.device_id:
                        device = device_registry.devices.get(entity_entry.device_id)
                        if device:
                            area_id = device.area_id
                    if area_id and area_id in area_registry.areas:
                        area_name = area_registry.areas[area_id].name
                        sensors_by_area.setdefault(area_name, []).append(entity_id)

        return sensors_by_area

    async def _get_all_temperature_sensors(self) -> list[str]:
        """Get all temperature sensors."""
        entity_registry = async_get_entity_registry(self.hass)
        sensors: list[str] = []

        for entity_id, entity_entry in entity_registry.entities.items():
            if entity_entry.domain == "sensor":
                state = self.hass.states.get(entity_id)
                if (
                    state
                    and state.attributes.get("device_class")
                    == SensorDeviceClass.TEMPERATURE.value
                ):
                    sensors.append(entity_id)

        return sensors

    async def async_step_select(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Select areas and sensors."""
        sensors_by_area = await self._get_sensors_by_area()

        if not sensors_by_area:
            # Check if there are any temperature sensors at all
            all_sensors = await self._get_all_temperature_sensors()
            if not all_sensors:
                return self.async_abort(reason="no_sensors")
            # If sensors exist but not assigned to areas, show a different step
            return await self.async_step_manual_select()

        if user_input is not None:
            # Collect selected sensors
            selected_areas: dict[str, list[str]] = {}
            for area_name in sensors_by_area:
                area_key = area_name.lower().replace(" ", "_")
                selected_sensors = user_input.get(area_key, [])
                if selected_sensors:
                    selected_areas[area_name] = selected_sensors

            return self.async_create_entry(
                title="Area Average Temperature",
                data={"areas": selected_areas},
            )

        # Build schema
        schema_dict = {}
        for area_name, sensors in sensors_by_area.items():
            area_key = area_name.lower().replace(" ", "_")
            options = []
            for sensor in sensors:
                state = self.hass.states.get(sensor)
                label = state.name if state else sensor
                options.append({"value": sensor, "label": label})
            schema_dict[vol.Optional(area_key, default=sensors)] = SelectSelector(
                SelectSelectorConfig(
                    options=options,
                    multiple=True,
                    mode="list",
                )
            )

        schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="select",
            data_schema=schema,
        )

    async def async_step_manual_select(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manual area creation when sensors aren't assigned to HA areas."""
        if user_input is not None:
            area_name = user_input["area_name"]
            selected_sensors = user_input["sensors"]

            if area_name and selected_sensors:
                return self.async_create_entry(
                    title="Area Average Temperature",
                    data={"areas": {area_name: selected_sensors}},
                )

        schema = vol.Schema(
            {
                vol.Required("area_name", default="Living Room"): TextSelector(),
                vol.Required("sensors"): EntitySelector(
                    EntitySelectorConfig(
                        device_class=SensorDeviceClass.TEMPERATURE,
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="manual_select",
            data_schema=schema,
        )


class AreaAverageTemperatureOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Area Average Temperature."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._areas: dict[str, list[str]] = dict(
            config_entry.options.get("areas", config_entry.data.get("areas", {}))
        )
        self._current_area: str | None = None

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_area", "edit_area", "remove_area"],
        )

    async def async_step_add_area(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Add a new area."""
        errors: dict[str, str] = {}

        if user_input is not None:
            area_name = user_input["area_name"].strip()

            # Validate area name
            if not area_name:
                errors["area_name"] = "invalid_name"
            elif area_name in self._areas:
                errors["area_name"] = "area_exists"
            else:
                # Move to sensor selection
                self._current_area = area_name
                return await self.async_step_add_area_sensors()

        schema = vol.Schema(
            {
                vol.Required("area_name"): TextSelector(),
            }
        )

        return self.async_show_form(
            step_id="add_area",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_add_area_sensors(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Select sensors for the new area."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_sensors = user_input.get("sensors", [])

            if not selected_sensors:
                errors["sensors"] = "no_sensors_selected"
            elif self._current_area:
                # Save the new area
                self._areas[self._current_area] = selected_sensors
                self._current_area = None
                return self.async_create_entry(data={"areas": self._areas})

        schema = vol.Schema(
            {
                vol.Required("sensors"): EntitySelector(
                    EntitySelectorConfig(
                        device_class=SensorDeviceClass.TEMPERATURE,
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="add_area_sensors",
            data_schema=schema,
            errors=errors,
            description_placeholders={"area_name": self._current_area or ""},
        )

    async def async_step_edit_area(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Select which area to edit."""
        if not self._areas:
            return self.async_show_form(
                step_id="edit_area",
                errors={"base": "no_areas_configured"},
            )

        if user_input is not None:
            self._current_area = user_input["area_key"]
            return await self.async_step_edit_area_sensors()

        area_options = [
            {"value": area_name, "label": area_name} for area_name in self._areas
        ]

        schema = vol.Schema(
            {
                vol.Required("area_key"): SelectSelector(
                    SelectSelectorConfig(
                        options=area_options,
                        mode="dropdown",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="edit_area",
            data_schema=schema,
        )

    async def async_step_edit_area_sensors(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Edit sensors for the selected area."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_sensors = user_input.get("sensors", [])

            if not selected_sensors:
                errors["sensors"] = "no_sensors_selected"
            elif self._current_area:
                # Update the area sensors
                self._areas[self._current_area] = selected_sensors
                self._current_area = None
                return self.async_create_entry(data={"areas": self._areas})

        current_sensors = self._areas.get(self._current_area, [])

        schema = vol.Schema(
            {
                vol.Required("sensors", default=current_sensors): EntitySelector(
                    EntitySelectorConfig(
                        device_class=SensorDeviceClass.TEMPERATURE,
                        multiple=True,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="edit_area_sensors",
            data_schema=schema,
            errors=errors,
            description_placeholders={"area_name": self._current_area or ""},
        )

    async def async_step_remove_area(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Remove an area."""
        if not self._areas:
            return self.async_show_form(
                step_id="remove_area",
                errors={"base": "no_areas_configured"},
            )

        if user_input is not None:
            area_to_remove = user_input["area_key"]

            if area_to_remove in self._areas:
                del self._areas[area_to_remove]
                return self.async_create_entry(data={"areas": self._areas})

        area_options = [
            {"value": area_name, "label": area_name} for area_name in self._areas
        ]

        schema = vol.Schema(
            {
                vol.Required("area_key"): SelectSelector(
                    SelectSelectorConfig(
                        options=area_options,
                        mode="dropdown",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="remove_area",
            data_schema=schema,
        )
