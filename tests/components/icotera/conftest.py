"""Common fixtures for the Icotera tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.icotera.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.icotera.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
        title="1.1.1.1",
    )


@pytest.fixture
def mock_icotera_client() -> Generator[AsyncMock]:
    """Mock an IcoteraApiClient."""
    with patch(
        "homeassistant.components.icotera.IcoteraApiClient", autospec=True
    ) as mock_client:
        client = mock_client.return_value
        client.login.return_value = True
        client.get_connected_devices.return_value = {
            "00:11:22:33:44:55": {
                "hostname": "device1",
                "ipv4_address": "192.168.1.10",
            },
            "66:77:88:99:aa:bb": {
                "hostname": "device2",
                "ipv4_address": "192.168.1.11",
            },
        }
        yield client
