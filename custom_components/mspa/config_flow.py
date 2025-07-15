from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN, API_BASE_URL
from .mspaapi import MSPAAPI, MSPAAPIException



_LOGGER = logging.getLogger(__name__)


class MSPAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MSpa integration."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices = None
        self.selected_device = None

    async def async_step_user(self, user_input=None):
        """Handle the user step of the config flow."""
        errors = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]

            # Test authentication and discover devices
            try:
                _LOGGER.info("Attempting login and device discovery")
                api = MSPAAPI(
                    base_url=API_BASE_URL,
                    username=username,
                    password=password
                )
                
                # Authenticate with username/password
                _LOGGER.info("Attempting login with username/password")
                await api.login()
                
                # Discover devices
                devices = await api.get_user_devices()
                await api.close()
                
                if not devices:
                    _LOGGER.error("No devices found for this account")
                    errors["base"] = "no_devices"
                elif len(devices) == 1:
                    # Only one device, proceed directly
                    device = devices[0]
                    data = {
                        "username": username,
                        "password": password,
                        "device_id": device["device_id"],
                        "product_id": device["product_id"],
                        "device_name": device["name"]
                    }
                    return self.async_create_entry(title=f"MSpa {device['name']}", data=data)
                else:
                    # Multiple devices, show selection step
                    self.discovered_devices = devices
                    return await self.async_step_device_selection()
                    
            except MSPAAPIException as e:
                _LOGGER.error("Connection failed with exception: %s", e)
                if "signature" in str(e).lower():
                    errors["base"] = "signature_failed"
                else:
                    errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("Unexpected error during connection test: %s", e)
                errors["base"] = "cannot_connect"

        # Simplified data schema - only username and password required
        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "username": "Your MSpa account username or email",
                "password": "Your MSpa account password",
            },
        )

    async def async_step_device_selection(self, user_input=None):
        """Handle device selection when multiple devices are found."""
        if user_input is not None:
            device_id = user_input["device"]
            # Find the selected device
            selected_device = next((d for d in self.discovered_devices if d["device_id"] == device_id), None)
            if selected_device:
                data = {
                    "username": user_input.get("username", ""),
                    "password": user_input.get("password", ""),
                    "device_id": selected_device["device_id"],
                    "product_id": selected_device["product_id"],
                    "device_name": selected_device["name"]
                }
                return self.async_create_entry(title=f"MSpa {selected_device['name']}", data=data)

        # Create device selection options
        device_options = {}
        for device in self.discovered_devices:
            status = "Online" if device["is_online"] else "Offline"
            device_options[device["device_id"]] = f"{device['name']} ({device['product_model']}) - {status}"

        data_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(device_options),
            }
        )

        return self.async_show_form(
            step_id="device_selection",
            data_schema=data_schema,
            description_placeholders={
                "device": "Select your MSpa device",
            },
        )