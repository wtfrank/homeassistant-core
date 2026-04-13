"""DataUpdateCoordinator for Icotera."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IcoteraApiClient, IcoteraAuthError, IcoteraConnectionError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IcoteraDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Class to manage fetching data from the Icotera router."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api: IcoteraApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Update data via the api."""
        try:
            return await self.api.get_connected_devices()
        except IcoteraAuthError as err:
            raise UpdateFailed(f"Invalid authentication: {err}") from err
        except IcoteraConnectionError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
