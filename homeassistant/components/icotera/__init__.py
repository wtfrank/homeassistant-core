"""The Icotera integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IcoteraApiClient
from .coordinator import IcoteraDataUpdateCoordinator

_PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER]

type IcoteraConfigEntry = ConfigEntry[IcoteraDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: IcoteraConfigEntry) -> bool:
    """Set up Icotera from a config entry."""
    session = async_get_clientsession(hass)
    api = IcoteraApiClient(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        session,
    )

    coordinator = IcoteraDataUpdateCoordinator(hass, entry, api)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: IcoteraConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
