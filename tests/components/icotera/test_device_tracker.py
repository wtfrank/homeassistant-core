"""Tests for the Icotera device tracker."""

from homeassistant.components.icotera.const import DOMAIN
from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry


async def test_device_tracker(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_icotera_client,
) -> None:
    """Test device tracker entities."""
    mock_config_entry.add_to_hass(hass)

    # Pre-register entities to ensure they are enabled
    registry = er.async_get(hass)
    entity_id1 = registry.async_get_or_create(
        "device_tracker", DOMAIN, "aa:bb:cc:dd:ee:01"
    ).entity_id
    entity_id2 = registry.async_get_or_create(
        "device_tracker", DOMAIN, "aa:bb:cc:dd:ee:02"
    ).entity_id

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state1 = hass.states.get(entity_id1)
    assert state1
    assert state1.state == STATE_HOME
    assert state1.attributes["ip"] == "192.168.1.112"
    assert state1.attributes["mac"] == "aa:bb:cc:dd:ee:01"
    assert state1.name == "Cerulean"

    state2 = hass.states.get(entity_id2)
    assert state2
    assert state2.state == STATE_HOME
    assert state2.attributes["ip"] == "192.168.1.247"
    assert state2.attributes["mac"] == "aa:bb:cc:dd:ee:02"
    assert state2.name == "Vermilion"

    # Test device removed
    mock_icotera_client.get_connected_devices.return_value = {
        "aa:bb:cc:dd:ee:01": {
            "hostname": "Cerulean",
            "ipv4_address": "192.168.1.112",
        },
    }

    # Simpler: call refresh directly on the coordinator
    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state1 = hass.states.get(entity_id1)
    assert state1.state == STATE_HOME

    state2 = hass.states.get(entity_id2)
    assert state2.state == STATE_NOT_HOME
