import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up the MSpa binary sensor platform."""
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

    # Define the binary sensors you want to create
    binary_sensors = [
        MSpABinarySensor(coordinator, "heater_state", "Heater"),
        MSpABinarySensor(coordinator, "filter_state", "Filter"),
        MSpABinarySensor(coordinator, "bubble_state", "Bubbles"),
        MSpABinarySensor(coordinator, "ozone_state", "Ozone"),
        MSpABinarySensor(coordinator, "uvc_state", "UVC"),
        MSpABinarySensor(coordinator, "jet_state", "Jet"),
        MSpABinarySensor(coordinator, "safety_lock", "Safety Lock"),
    ]

    async_add_entities(binary_sensors)


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


class MSpABinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MSpa binary sensor."""

    def __init__(self, coordinator: MSPADataUpdateCoordinator, data_key: str, name: str):
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
