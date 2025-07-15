import logging
import asyncio
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, API_BASE_URL
from .mspaapi import MSPAAPI, MSPAAPIException

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=15)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MSpa sensor platform."""
    username = config_entry.data["username"]
    password = config_entry.data["password"]
    device_id = config_entry.data["device_id"]
    product_id = config_entry.data["product_id"]
    access_token = config_entry.data.get("access_token")
    
    api = MSPAAPI(
        base_url=API_BASE_URL,
        device_id=device_id,
        product_id=product_id,
        username=username,
        password=password,
        access_token=access_token
    )

    # Create a coordinator to manage data updates
    coordinator = MSPADataUpdateCoordinator(hass, api)
    await coordinator.async_refresh()

    async_add_entities([
        MSpANumericSensor(coordinator, "water_temperature", "Water Temperature"),
        MSpANumericSensor(coordinator, "temperature_setting", "Target Temperature"),
        MSpABubbleSensor(coordinator)
    ])


class MSPADataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, api: MSPAAPI):
        """Initialize the data update coordinator."""
        self._api = api
        super().__init__(
            hass,
            _LOGGER,
            name="MSPADataUpdateCoordinator",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from the API."""
        try:
            data = await self._api.get_device_status()
            _LOGGER.debug("Fetched MSpa data: %s", data)
            return data
        except MSPAAPIException as e:
            _LOGGER.error("Error fetching MSpa data: %s", e)
            return {}


class MSpANumericSensor(CoordinatorEntity, SensorEntity):
    """Representation of a MSpa numeric sensor."""

    def __init__(self, coordinator: MSPADataUpdateCoordinator, data_key: str, name: str):
        """Initialize the MSpa numeric sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"mspa_{coordinator._api.device_id}_{data_key}"
        if data_key == "water_temperature":
            self._attr_icon = "mdi:thermometer-water"
        elif data_key == "temperature_setting":
            self._attr_icon = "mdi:thermostat"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._data_key in self.coordinator.data:
            # API returns doubled Celsius values, so divide by 2 to get actual Celsius
            celsius_temp = self.coordinator.data[self._data_key] * 0.5
            
            # Convert to system unit preference
            if self.hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT:
                return TemperatureConverter.convert(celsius_temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT)
            return celsius_temp
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self.hass.config.units.temperature_unit


class MSpABubbleSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MSpa bubble state sensor."""

    def __init__(self, coordinator: MSPADataUpdateCoordinator):
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
