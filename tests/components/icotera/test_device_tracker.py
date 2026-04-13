"""Tests for the Icotera device tracker."""

from unittest.mock import patch

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
        "device_tracker", DOMAIN, "00:11:22:33:44:55"
    ).entity_id
    entity_id2 = registry.async_get_or_create(
        "device_tracker", DOMAIN, "66:77:88:99:aa:bb"
    ).entity_id

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state1 = hass.states.get(entity_id1)
    assert state1
    assert state1.state == STATE_HOME
    assert state1.attributes["ip"] == "192.168.1.10"
    assert state1.attributes["mac"] == "00:11:22:33:44:55"

    state2 = hass.states.get(entity_id2)
    assert state2
    assert state2.state == STATE_HOME
    assert state2.attributes["ip"] == "192.168.1.11"
    assert state2.attributes["mac"] == "66:77:88:99:aa:bb"

    # Test device removed
    mock_icotera_client.get_connected_devices.return_value = {
        "00:11:22:33:44:55": {
            "hostname": "device1",
            "ipv4_address": "192.168.1.10",
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
