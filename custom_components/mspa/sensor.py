import logging
import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
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
    """Set up the MSpa sensor platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    async_add_entities([
        MSpANumericSensor(coordinator, "water_temperature", "Water Temperature"),
        MSpANumericSensor(coordinator, "temperature_setting", "Target Temperature"),
        MSpABubbleSensor(coordinator)
    ])




class MSpANumericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a MSpa numeric sensor."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", data_key: str, name: str):
        """Initialize the MSpa numeric sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"mspa_{coordinator._api.device_id}_{data_key}"
        if data_key == "water_temperature":
            self._attr_icon = "mdi:thermometer"
        elif data_key == "temperature_setting":
            self._attr_icon = "mdi:thermostat"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._data_key in self.coordinator.data:
            return self.coordinator.data[self._data_key] * 0.5  # Apply correction factor
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return UnitOfTemperature.CELSIUS


class MSpABubbleSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MSpa bubble state sensor."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator"):
        """Initialize the bubble sensor."""
        super().__init__(coordinator)
        self._attr_name = "Bubble Level"
        self._attr_unique_id = f"mspa_{coordinator._api.device_id}_bubble_level"
        self._attr_icon = "mdi:chart-bubble"

    @property
    def state(self):
        """Return the current bubble level."""
        if "bubble_level" in self.coordinator.data:
            bubble_state = self.coordinator.data["bubble_level"]
            return {
                0: "Off",
                1: "Low",
                2: "Medium",
                3: "High",
            }.get(bubble_state, "Unknown")
        return None
