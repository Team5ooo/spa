import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
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
    """Set up the MSpa button platform."""
    # Get shared coordinator and API from hass.data
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([
        MSpaBubbleButton(coordinator, api),
    ])


class MSpaBubbleButton(CoordinatorEntity, ButtonEntity):
    """Button to cycle through bubble levels: Low -> Medium -> High -> Low (only when bubbles are on)."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI):
        """Initialize the bubble level button."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Bubble Level"
        self._attr_unique_id = f"mspa_{api.device_id}_bubble_level_button"
        self._attr_icon = "mdi:gesture-tap"

    @property
    def available(self) -> bool:
        """Return True if entity is available and bubbles are on."""
        bubble_state = self.coordinator.data.get("bubble_state", 0)
        return bool(self.coordinator.data) and bubble_state == 1

    async def async_press(self) -> None:
        """Cycle through bubble levels: Low (1) -> Medium (2) -> High (3) -> Low (1)."""
        try:
            # Only change level if bubbles are currently on
            bubble_state = self.coordinator.data.get("bubble_state", 0)
            if bubble_state != 1:
                _LOGGER.info("Bubbles are off, turn on bubbles first to change level")
                return

            current_level = self.coordinator.data.get("bubble_level", 1)
            
            # Cycle through levels: 1->2->3->1 (Low->Medium->High->Low)
            new_level = (current_level % 3) + 1
            
            # Only change bubble_level, don't touch bubble_state
            desired_state = {"bubble_level": new_level}
            
            # Optimistic update - update coordinator data immediately
            if hasattr(self.coordinator, 'data') and self.coordinator.data:
                self.coordinator.data["bubble_level"] = new_level
                self.coordinator.async_set_updated_data(self.coordinator.data)
            
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa bubble level command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                await self.coordinator.async_request_refresh()
                level_names = {1: "Low", 2: "Medium", 3: "High"}
                _LOGGER.debug(f"Changed bubble level to {level_names.get(new_level, new_level)}.")
            else:
                _LOGGER.warning(f"Unexpected MSpa bubble level response: {response}")
                # Revert optimistic update on failure
                await self.coordinator.async_request_refresh()

        except MSPAAPIException as e:
            _LOGGER.error("Error setting bubble level: %s", e)
            # Revert optimistic update on error
            await self.coordinator.async_request_refresh()