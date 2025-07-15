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

    async def async_step_user(self, user_input=None):
        """Handle the user step of the config flow."""
        errors = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]
            device_id = user_input["device_id"]
            product_id = user_input["product_id"]
            access_token = user_input.get("access_token")

            # Test the connection using the provided credentials
            try:
                _LOGGER.info("Testing connection for device: %s", device_id)
                api = MSPAAPI(
                    base_url=API_BASE_URL,
                    device_id=device_id,
                    product_id=product_id,
                    username=username,
                    password=password,
                    access_token=access_token
                )
                
                # Test authentication and connection
                if access_token:
                    _LOGGER.info("Using manual access token")
                    connection_status = await api.test_connection()
                else:
                    _LOGGER.info("Attempting login with username/password")
                    await api.login()
                    connection_status = await api.test_connection()
                
                await api.close()
                
                if connection_status:
                    _LOGGER.info("Connection successful!")
                else:
                    _LOGGER.error("Connection failed.")
                    errors["base"] = "cannot_connect"
            except MSPAAPIException as e:
                _LOGGER.error("Connection failed with exception: %s", e)
                if "signature" in str(e).lower():
                    errors["base"] = "signature_failed"
                else:
                    errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("Unexpected error during connection test: %s", e)
                errors["base"] = "cannot_connect"

            if not errors:
                # If there are no errors, store the input and proceed
                return self.async_create_entry(title=f"MSpa {device_id}", data=user_input)

      # Dynamically create the data schema to use values from strings.json

        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
                vol.Required("device_id"): str,
                vol.Required("product_id"): str,
                vol.Optional("access_token", description="Manual token (fallback if login fails)"): str,
            }
        )



        #return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "username": "Your MSpa account username or email",
                "password": "Your MSpa account password",
                "device_id": "The ID of your MSpa device",
                "product_id": "The product ID of your MSpa device",
            },
        )