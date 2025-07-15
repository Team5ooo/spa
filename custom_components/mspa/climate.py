import asyncio
import logging
from datetime import timedelta
from typing import Any, TYPE_CHECKING

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    """Set up the MSpa climate platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([
        MSpaClimate(coordinator, api),
    ])




class MSpaClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a MSpa climate control."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI):
        """Initialize the MSpa climate control."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "MSpa Temperature"
        self._attr_unique_id = f"mspa_{api.device_id}_climate"
        self._attr_icon = "mdi:hot-tub"
        
        # Climate entity features
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        
        # HVAC modes
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        
        # Temperature settings
        self._attr_min_temp = 20  # 20°C / 68°F
        self._attr_max_temp = 40  # 40°C / 104°F
        self._attr_target_temperature_step = 0.5  # 0.5°C increments

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        # Check if device is set to Fahrenheit (1) or Celsius (0)
        temp_unit = self.coordinator.data.get("temperature_unit", 0)
        return UnitOfTemperature.FAHRENHEIT if temp_unit == 1 else UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if "water_temperature" in self.coordinator.data:
            # Apply correction factor (device reports in 0.5°C increments)
            temp_celsius = self.coordinator.data["water_temperature"] * 0.5
            
            # Convert to Fahrenheit if device is set to Fahrenheit
            if self.coordinator.data.get("temperature_unit", 0) == 1:
                return round(temp_celsius * 9/5 + 32, 1)
            return round(temp_celsius, 1)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if "temperature_setting" in self.coordinator.data:
            # The API expects/returns actual temperature values, not the 0.5 factor
            temp_celsius = self.coordinator.data["temperature_setting"]
            
            # Convert to Fahrenheit if device is set to Fahrenheit
            if self.coordinator.data.get("temperature_unit", 0) == 1:
                return round(temp_celsius * 9/5 + 32, 1)
            return round(temp_celsius, 1)
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        heater_state = self.coordinator.data.get("heater_state", 0)
        return HVACMode.HEAT if heater_state == 1 else HVACMode.OFF

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            return

        try:
            # The MSpa API always expects temperature in Celsius, regardless of display unit
            # Home Assistant sends temperature in the unit specified by temperature_unit property
            temp_celsius = temperature
            
            # If HA is sending Fahrenheit (because our temperature_unit is Fahrenheit),
            # we need to convert to Celsius for the API
            if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
                temp_celsius = (temperature - 32) * 5/9

            # Round to nearest half degree (0.5°C increments) and ensure within valid range (20-40°C)
            temp_celsius = round(temp_celsius * 2) / 2
            temp_celsius = max(20, min(40, temp_celsius))

            desired_state = {"temperature_setting": temp_celsius}
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa temperature command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Immediately refresh data from API to get real device state
                await self.coordinator.async_request_refresh()
                _LOGGER.debug("Triggered immediate refresh after temperature change.")
            else:
                _LOGGER.warning(f"Unexpected MSpa temperature command response: {response}")

        except MSPAAPIException as e:
            _LOGGER.error("Error setting MSpa temperature: %s", e)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        try:
            if hvac_mode == HVACMode.HEAT:
                # Turn on heater (and filter as dependency)
                desired_state = {"heater_state": 1, "filter_state": 1}
            elif hvac_mode == HVACMode.OFF:
                # Turn off heater only
                desired_state = {"heater_state": 0}
            else:
                _LOGGER.warning(f"Unsupported HVAC mode: {hvac_mode}")
                return

            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa HVAC command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Immediately refresh data from API to get real device state
                await self.coordinator.async_request_refresh()
                _LOGGER.debug("Triggered immediate refresh after HVAC mode change.")
            else:
                _LOGGER.warning(f"Unexpected MSpa HVAC command response: {response}")

        except MSPAAPIException as e:
            _LOGGER.error("Error setting MSpa HVAC mode: %s", e)