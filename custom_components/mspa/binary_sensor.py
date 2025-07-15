import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up the MSpa binary sensor platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]

    # Define the binary sensors you want to create
    # Only include read-only sensors (jet_state is read-only, others are controllable via switches)
    binary_sensors = [
        MSpABinarySensor(coordinator, "jet_state", "Jet"),
    ]

    async_add_entities(binary_sensors)




class MSpABinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MSpa binary sensor."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", data_key: str, name: str):
        """Initialize the MSpa binary sensor."""
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"mspa_{coordinator._api.device_id}_{data_key}_binary"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self.coordinator.data.get(self._data_key, False)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)
