"""The MSpa integration."""

from __future__ import annotations
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, API_BASE_URL
from .mspaapi import MSPAAPI, MSPAAPIException

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR,Platform.SWITCH,Platform.CLIMATE,Platform.SELECT]

SCAN_INTERVAL = timedelta(minutes=15)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MSpa from a config entry."""
    
    # Get configuration data
    username = entry.data["username"]
    password = entry.data["password"]
    device_id = entry.data["device_id"]
    product_id = entry.data["product_id"]
    access_token = entry.data.get("access_token")
    
    # Create API instance
    api = MSPAAPI(
        base_url=API_BASE_URL,
        device_id=device_id,
        product_id=product_id,
        username=username,
        password=password,
        access_token=access_token
    )

    # Create shared coordinator
    coordinator = MSPADataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in hass.data for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up stored data
        if DOMAIN in hass.data:
            hass.data[DOMAIN].pop(entry.entry_id, None)
            
            # Clean up domain data if no more entries
            if not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN)
    
    return unload_ok


class MSPADataUpdateCoordinator(DataUpdateCoordinator):
    """Shared coordinator to manage fetching data from the API."""

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
