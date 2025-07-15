import asyncio
import logging
from datetime import timedelta
import json

import aiohttp
from homeassistant.components.switch import SwitchEntity
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
    """Set up the MSpa switch platform."""
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
    await coordinator.async_config_entry_first_refresh()

    # Define the switches you want to create
    switches = [
        MSpASwitch(coordinator, api, "heater_state", "Heater"),
        MSpASwitch(coordinator, api, "filter_state", "Filter"),
        MSpASwitch(coordinator, api, "bubble_state", "Bubbles State"),
        MSpASwitch(coordinator, api, "ozone_state", "Ozone"),
        MSpASwitch(coordinator, api, "uvc_state", "UVC"),
       # MSpASwitch(coordinator, api, "jet_state", "Jet"),
        MSpASwitch(coordinator, api, "safety_lock", "Safety Lock"),
    ]

    # Add entities to hass.data for easier access in async_turn_on and async_turn_off
    hass.data.setdefault(DOMAIN, {}).setdefault("entities", []).extend(switches)

    async_add_entities(switches)



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
        """Fetch data from the API at regular intervals."""
        try:
            data = await self._api.get_device_status()
            _LOGGER.debug("Fetched MSpa data: %s", data)
            return data
        except MSPAAPIException as e:
            _LOGGER.error("Error fetching MSpa data: %s", e)
            return self.data  # Return existing data if fetch fails




class MSpASwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a MSpa switch."""

    def __init__(self, coordinator: MSPADataUpdateCoordinator, api: MSPAAPI, data_key: str, name: str):
        """Initialize the MSpa switch."""
        super().__init__(coordinator)
        self._api = api
        self._data_key = data_key
        self._attr_name = name
        self._attr_unique_id = f"mspa_{api.device_id}_{data_key}_switch"

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

            # Set bubble_level if turning on bubbles
            if self._data_key == "bubble_state":
                bubble_level = self.coordinator.data.get("bubble_level", 2)  # Use the last known bubble level or default to 2
                desired_state["bubble_level"] = bubble_level

            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                # Immediately refresh data from API to get real device state
                await self.coordinator.async_request_refresh()
                _LOGGER.debug("Triggered immediate refresh after successful turn_on command.")
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
                # Immediately refresh data from API to get real device state
                await self.coordinator.async_request_refresh()
                _LOGGER.debug("Triggered immediate refresh after successful turn_off command.")
            else:
                _LOGGER.warning(f"Unexpected MSpa command response: {response}")
        except MSPAAPIException as e:
            _LOGGER.error("Error turning off MSpa switch: %s", e)