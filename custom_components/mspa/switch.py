import logging
from datetime import timedelta
import json
from typing import TYPE_CHECKING

import aiohttp
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, API_BASE_URL
from .mspaapi import MSPAAPI, MSPAAPIException

if TYPE_CHECKING:
    from . import MSPADataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MSpa switch platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    # Define the switches you want to create
    switches = [
        MSpASwitch(coordinator, api, "heater_state", "Heater"),
        MSpASwitch(coordinator, api, "filter_state", "Filter"),
        MSpASwitch(coordinator, api, "bubble_state", "Bubbles"),
        MSpASwitch(coordinator, api, "ozone_state", "Ozone"),
        MSpASwitch(coordinator, api, "uvc_state", "UVC"),
       # MSpASwitch(coordinator, api, "jet_state", "Jet"),
        MSpASwitch(coordinator, api, "safety_lock", "Safety Lock"),
        MSpaTemperatureUnitSwitch(coordinator, api),
    ]

    # Add entities to hass.data for easier access in async_turn_on and async_turn_off
    hass.data.setdefault(DOMAIN, {}).setdefault("entities", []).extend(switches)

    async_add_entities(switches)






class MSpASwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a MSpa switch."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI, data_key: str, name: str):
        """Initialize the MSpa switch."""
        super().__init__(coordinator)
        self._api = api
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"mspa_{api.device_id}_{data_key}_switch"
        
        # Set descriptive icons based on switch type
        icon_map = {
            "heater_state": "mdi:fire",
            "filter_state": "mdi:air-filter",
            "bubble_state": "mdi:bubble",
            "ozone_state": "mdi:molecule",
            "uvc_state": "mdi:lightbulb-on",
            "safety_lock": "mdi:lock",
            "jet_state": "mdi:hydro-power"
        }
        self._attr_icon = icon_map.get(data_key, "mdi:power")

    @property
    def is_on(self):
        """Return True if the switch is on."""
        return self.coordinator.data.get(self._data_key, 0) == 1  # Check if value is 1

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        try:
            desired_state = {self._data_key: 1}

            # Check if turning on heater or uvc_state requires filter_state to be on
            if self._data_key in ["heater_state", "uvc_state"]:
                desired_state["filter_state"] = 1

            # Set bubble_level when turning on bubbles
            if self._data_key == "bubble_state":
                bubble_level = self.coordinator.data.get("bubble_level", 1)  # Default to Low if not set
                desired_state["bubble_level"] = bubble_level

            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Optimistic update - immediately update coordinator data
                if hasattr(self.coordinator, 'data') and self.coordinator.data:
                    for key, value in desired_state.items():
                        self.coordinator.data[key] = value
                    self.coordinator.async_set_updated_data(self.coordinator.data)
                _LOGGER.debug(f"Optimistically updated {self._data_key} to ON")
            else:
                _LOGGER.warning(f"Unexpected MSpa command response: {response}")

        except MSPAAPIException as e:
            _LOGGER.error("Error turning on MSpa switch: %s", e)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        try:
            desired_state = {self._data_key: 0}

            # Check if turning off filter requires turning off heater, ozone, and uvc
            if self._data_key == "filter_state":
                dependencies = ["heater_state", "ozone_state", "uvc_state"]
                for dep in dependencies:
                    desired_state[dep] = 0

            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa command response: {response}")
            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Optimistic update - immediately update coordinator data
                if hasattr(self.coordinator, 'data') and self.coordinator.data:
                    for key, value in desired_state.items():
                        self.coordinator.data[key] = value
                    self.coordinator.async_set_updated_data(self.coordinator.data)
                _LOGGER.debug(f"Optimistically updated {self._data_key} to OFF")
            else:
                _LOGGER.warning(f"Unexpected MSpa command response: {response}")
        except MSPAAPIException as e:
            _LOGGER.error("Error turning off MSpa switch: %s", e)


class MSpaTemperatureUnitSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to toggle between Celsius and Fahrenheit."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI):
        """Initialize the temperature unit switch."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Temperature Unit (°F)"
        self._attr_unique_id = f"mspa_{api.device_id}_temperature_unit"
        # Dynamic icon will be set in the icon property

    @property
    def is_on(self):
        """Return True if set to Fahrenheit (1), False if Celsius (0)."""
        return self.coordinator.data.get("temperature_unit", 0) == 1

    @property
    def icon(self):
        """Return dynamic icon based on current temperature unit."""
        if self.coordinator.data.get("temperature_unit", 0) == 1:
            return "mdi:temperature-fahrenheit"
        return "mdi:temperature-celsius"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    async def async_turn_on(self, **kwargs):
        """Set temperature unit to Fahrenheit."""
        try:
            desired_state = {"temperature_unit": 1}
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa temperature unit command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Optimistic update - immediately update coordinator data
                if hasattr(self.coordinator, 'data') and self.coordinator.data:
                    self.coordinator.data["temperature_unit"] = 1
                    self.coordinator.async_set_updated_data(self.coordinator.data)
                _LOGGER.debug("Optimistically set temperature unit to Fahrenheit.")
            else:
                _LOGGER.warning(f"Unexpected MSpa temperature unit response: {response}")

        except MSPAAPIException as e:
            _LOGGER.error("Error setting temperature unit to Fahrenheit: %s", e)

    async def async_turn_off(self, **kwargs):
        """Set temperature unit to Celsius."""
        try:
            desired_state = {"temperature_unit": 0}
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa temperature unit command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Optimistic update - immediately update coordinator data
                if hasattr(self.coordinator, 'data') and self.coordinator.data:
                    self.coordinator.data["temperature_unit"] = 0
                    self.coordinator.async_set_updated_data(self.coordinator.data)
                _LOGGER.debug("Optimistically set temperature unit to Celsius.")
            else:
                _LOGGER.warning(f"Unexpected MSpa temperature unit response: {response}")

        except MSPAAPIException as e:
            _LOGGER.error("Error setting temperature unit to Celsius: %s", e)


