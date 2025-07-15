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
    """Button to cycle through bubble levels: Off -> Low -> Medium -> High -> Off."""

    def __init__(self, coordinator: "MSPADataUpdateCoordinator", api: MSPAAPI):
        """Initialize the bubble button."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Bubbles"
        self._attr_unique_id = f"mspa_{api.device_id}_bubble_button"
        self._attr_icon = "mdi:bubble"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self.coordinator.data)

    async def async_press(self) -> None:
        """Cycle through bubble levels: Off (0) -> Low (1) -> Medium (2) -> High (3) -> Off (0)."""
        try:
            current_level = self.coordinator.data.get("bubble_level", 0)
            
            # Cycle through levels: 0->1->2->3->0
            new_level = (current_level + 1) % 4
            
            # Determine bubble state based on level
            if new_level == 0:
                # Off
                desired_state = {"bubble_state": 0, "bubble_level": 0}
            else:
                # Low (1), Medium (2), High (3)
                desired_state = {"bubble_state": 1, "bubble_level": new_level}
            
            # Optimistic update - update coordinator data immediately
            if hasattr(self.coordinator, 'data') and self.coordinator.data:
                self.coordinator.data["bubble_level"] = new_level
                self.coordinator.data["bubble_state"] = 1 if new_level > 0 else 0
                self.coordinator.async_set_updated_data(self.coordinator.data)
            
            response = await self._api.send_device_command(desired_state)
            _LOGGER.debug(f"MSpa bubble command response: {response}")

            if response.get("code") == 0 and response.get("message") == "SUCCESS":
                await self.coordinator.async_request_refresh()
                level_names = {0: "Off", 1: "Low", 2: "Medium", 3: "High"}
                _LOGGER.debug(f"Changed bubble level to {level_names.get(new_level, new_level)}.")
            else:
                _LOGGER.warning(f"Unexpected MSpa bubble response: {response}")
                # Revert optimistic update on failure
                await self.coordinator.async_request_refresh()

        except MSPAAPIException as e:
            _LOGGER.error("Error setting bubble level: %s", e)
            # Revert optimistic update on error
            await self.coordinator.async_request_refresh()