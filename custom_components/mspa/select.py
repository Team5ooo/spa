import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .mspaapi import MSPAAPI, MSPAAPIException

if TYPE_CHECKING:
    from . import MSPADataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MSpa select platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([
        MSpaBubbleLevelSelect(coordinator, api),
    ])


class MSpaBubbleLevelSelect(CoordinatorEntity, SelectEntity):
    """Select entity for bubble level control."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI):
        """Initialize the bubble level select."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Bubble Level"
        self._attr_unique_id = f"mspa_{api.device_id}_bubble_level_select"
        self._attr_icon = "mdi:chart-bubble"
        self._attr_options = ["Low", "Medium", "High"]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if "bubble_level" in self.coordinator.data:
            bubble_level = self.coordinator.data["bubble_level"]
            
            # Always show the last known bubble level regardless of bubble_state
            level_map = {1: "Low", 2: "Medium", 3: "High"}
            return level_map.get(bubble_level)
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            # Map option to bubble level
            option_map = {"Low": 1, "Medium": 2, "High": 3}
            new_level = option_map.get(option)
            
            if new_level is None:
                _LOGGER.error(f"Invalid bubble level option: {option}")
                return

            # Always turn on bubbles and set level
            desired_state = {
                "bubble_state": 1,
                "bubble_level": new_level
            }
            
            # Optimistic update - update coordinator data immediately
            if hasattr(self.coordinator, 'data') and self.coordinator.data:
                self.coordinator.data["bubble_level"] = new_level
                self.coordinator.data["bubble_state"] = 1
                self.coordinator.async_set_updated_data(self.coordinator.data)
            
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa bubble level select response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                _LOGGER.debug(f"Successfully changed bubble level to {option} and turned on bubbles.")
            else:
                _LOGGER.warning(f"Unexpected MSpa bubble level response: {response}")
                # Revert optimistic update on failure
                await self.coordinator.async_request_refresh()

        except MSPAAPIException as e:
            _LOGGER.error("Error setting bubble level: %s", e)
            # Revert optimistic update on error
            await self.coordinator.async_request_refresh()