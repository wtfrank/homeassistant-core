"""Device tracking presence support for Icotera routers."""

from __future__ import annotations

from homeassistant.components.device_tracker import ScannerEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IcoteraConfigEntry
from .coordinator import IcoteraDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IcoteraConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up device tracker for Icotera component."""
    coordinator = entry.runtime_data
    tracked: set[str] = set()

    @callback
    def update_entities() -> None:
        """Add new entities from the router."""
        new_entities = []
        for mac in coordinator.data:
            if mac not in tracked:
                new_entities.append(IcoteraDeviceTracker(coordinator, mac))
                tracked.add(mac)
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(update_entities))
    update_entities()


class IcoteraDeviceTracker(
    CoordinatorEntity[IcoteraDataUpdateCoordinator], ScannerEntity
):
    """Representation of an Icotera device."""

    _attr_entity_category = None

    def __init__(self, coordinator: IcoteraDataUpdateCoordinator, mac: str) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._mac = mac
        self._attr_unique_id = mac

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self.hostname or self._mac

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        return self._mac

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        return self._mac in self.coordinator.data

    @property
    def hostname(self) -> str | None:
        """Return the hostname of the device."""
        if device := self.coordinator.data.get(self._mac):
            return device.get("hostname")
        return None

    @property
    def ip_address(self) -> str | None:
        """Return the primary ip address of the device."""
        if device := self.coordinator.data.get(self._mac):
            return device.get("ipv4_address")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return the state attributes."""
        if device := self.coordinator.data.get(self._mac):
            return {
                "port": device.get("port"),
            }
        return {}
