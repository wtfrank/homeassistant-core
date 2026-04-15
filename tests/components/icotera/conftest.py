"""Common fixtures for the Icotera tests."""

from collections.abc import Generator
import json
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.icotera.api import IcoteraApiClient
from homeassistant.components.icotera.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from tests.common import MockConfigEntry, load_fixture


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

        # Load fixture data and parse it using the production parsing logic
        content = load_fixture("i4850-31/connected_devices.json", "icotera")
        data = json.loads(content)
        client.get_connected_devices.return_value = IcoteraApiClient._parse_devices(data)

        yield client
