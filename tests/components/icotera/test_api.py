"""Tests for the Icotera API client."""

from urllib.parse import quote
import pytest
from yarl import URL

from homeassistant.components.icotera.api import IcoteraApiClient, IcoteraAuthError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from tests.common import load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker, AiohttpClientMockResponse

async def test_login_success(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test successful login."""
    host = "1.1.1.1"
    url = f"http://{host}/index.cgi"
    yarl_url = URL(url)
    
    login_success_body = load_fixture("i4850-31/login_success.json", "icotera")

    async def side_effect(method, url, data):
        if "req=systeminfo_part1" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                json={"resp_t": "systeminfo_part1_resp"},
                headers={"Set-Cookie": "CGISID=test_session_id"},
            )
        if "req=log_in" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                text=login_success_body,
                headers={"Content-Type": "application/json"},
            )
        return None

    aioclient_mock.post(url, side_effect=side_effect)

    session = async_get_clientsession(hass)
    api = IcoteraApiClient(host, "admin", "password", session)
    
    assert await api.login() is True
    assert api._is_logged_in is True

async def test_login_failure(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test failed login."""
    host = "1.1.1.1"
    url = f"http://{host}/index.cgi"
    yarl_url = URL(url)
    
    login_failure_body = load_fixture("i4850-31/login_failure.json", "icotera")

    async def side_effect(method, url, data):
        if "req=systeminfo_part1" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                json={"resp_t": "systeminfo_part1_resp"},
                headers={"Set-Cookie": "CGISID=test_session_id"},
            )
        if "req=log_in" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                text=login_failure_body,
                headers={"Content-Type": "application/json"},
            )
        return None

    aioclient_mock.post(url, side_effect=side_effect)

    session = async_get_clientsession(hass)
    api = IcoteraApiClient(host, "admin", "wrong_password", session)
    
    with pytest.raises(IcoteraAuthError):
        await api.login()
    assert api._is_logged_in is False

async def test_login_html_response(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    """Test login receiving HTML instead of JSON."""
    host = "1.1.1.1"
    url = f"http://{host}/index.cgi"
    yarl_url = URL(url)
    
    async def side_effect(method, url, data):
        if "req=systeminfo_part1" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                json={"resp_t": "systeminfo_part1_resp"},
                headers={"Set-Cookie": "CGISID=test_session_id"},
            )
        if "req=log_in" in data:
            return AiohttpClientMockResponse(
                method, yarl_url,
                text="<html><body>Login Page</body></html>",
                headers={"Content-Type": "text/html"},
            )
        return None

    aioclient_mock.post(url, side_effect=side_effect)

    session = async_get_clientsession(hass)
    api = IcoteraApiClient(host, "admin", "password", session)
    
    with pytest.raises(IcoteraAuthError, match="Invalid credentials or session error"):
        await api.login()
