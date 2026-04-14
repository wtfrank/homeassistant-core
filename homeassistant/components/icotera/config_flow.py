"""Config flow for the Icotera integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

import aiohttp

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import IcoteraApiClient, IcoteraAuthError, IcoteraConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate that the user input allows us to connect to the router.
    """
    session = async_create_clientsession(
        hass, cookie_jar=aiohttp.CookieJar(unsafe=True)
    )
    api = IcoteraApiClient(
        data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD], session
    )

    try:
        await api.login()
    except IcoteraAuthError as err:
        raise InvalidAuth from err
    except IcoteraConnectionError as err:
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_HOST]}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the Icotera integratio."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect to the router."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
