"""Icotera API client."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from aiohttp import ClientResponseError, ClientSession

from homeassistant.helpers.device_registry import format_mac

_LOGGER = logging.getLogger(__name__)


class IcoteraAuthError(Exception):
    """Exception to indicate authentication error."""


class IcoteraConnectionError(Exception):
    """Exception to indicate connection error."""


class IcoteraApiClient:
    """Icotera API client."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._username = username
        self._password = password
        self._session = session
        self._url = f"http://{host}/index.cgi"
        self._is_logged_in = False

    async def login(self) -> bool:
        """Log in to the router."""
        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": f"http://{self._host}",
            "Referer": f"http://{self._host}/",
        }
        try:
            # get the session cookie (CGISID)
            initial_payload = "req=systeminfo_part1&opt=1&"
            async with self._session.post(
                self._url, data=initial_payload, headers=headers, timeout=10
            ) as response:
                _LOGGER.debug(
                    "Initial request sent: %s\nHeaders: %s\nResponse: %s",
                    initial_payload,
                    response.request_info.headers,
                    response.headers,
                )
                response.raise_for_status()

            # login
            login_payload = (
                f"curpg=null&req=log_in&username={quote(self._username)}&password={quote(self._password)}&"
            )
            async with self._session.post(
                self._url, data=login_payload, headers=headers, timeout=10
            ) as response:
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug(
                        "Login request sent: username=%s\nHeaders: %s\nResponse: %s\nCookies: %s",
                        self._username,
                        response.request_info.headers,
                        response.headers,
                        self._session.cookie_jar.filter_cookies(self._url),
                    )
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    _LOGGER.error("Login failed: Received HTML response")
                    raise IcoteraAuthError("Invalid credentials or session error")
                
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug("Login response body: %s", await response.text())
                
                # Verify JSON response has login_result and status 1
                try:
                    data = await response.json()
                    resp_t = data.get("resp_t")
                    status = data.get("resp_body", {}).get("status")
                    
                    if resp_t != "login_result" or status != "1":
                        _LOGGER.error("Login failed: Unexpected response structure or status (%s, %s)", resp_t, status)
                        raise IcoteraAuthError(f"Login failed: {resp_t} status {status}")
                except Exception as err:
                    if isinstance(err, IcoteraAuthError):
                        raise
                    _LOGGER.error("Error parsing login response: %s", err)
                    raise IcoteraAuthError("Invalid JSON in login response") from err

            self._is_logged_in = True
        except ClientResponseError as err:
            _LOGGER.error("HTTP error during login: %s", err)
            raise IcoteraConnectionError from err
        except (IcoteraAuthError, IcoteraConnectionError):
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error during login: %s", err)
            raise IcoteraConnectionError from err
        else:
            return True

    async def get_connected_devices(self) -> dict[str, dict[str, Any]]:
        """Get connected devices from the router."""
        if not self._is_logged_in:
            await self.login()

        headers = {
            "Content-Type": "text/plain;charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": f"http://{self._host}",
            "Referer": f"http://{self._host}/",
        }
        devices_payload = "curpg=status.connecteddevices&curmenu=STATUS/CONNECTED_DEVICES&req=ConnectedDevices_getDevice_all&"

        try:
            async with self._session.post(
                self._url, data=devices_payload, headers=headers, timeout=30
            ) as response:
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug(
                        "Device fetch request sent: %s\nHeaders: %s\nResponse: %s\nCookies: %s",
                        devices_payload,
                        response.request_info.headers,
                        response.headers,
                        self._session.cookie_jar.filter_cookies(self._url),
                    )
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    _LOGGER.debug("Session lost, re-authenticating")
                    self._is_logged_in = False
                    return await self.get_connected_devices()

                data = await response.json()
                _LOGGER.debug("Device fetch response: %s", data)
                return self._parse_devices(data)
        except ClientResponseError as err:
            _LOGGER.error("HTTP error fetching devices: %s", err)
            self._is_logged_in = False
            raise IcoteraConnectionError from err
        except Exception as err:
            _LOGGER.error("Error fetching devices: %s", err)
            self._is_logged_in = False
            raise IcoteraConnectionError from err

    @staticmethod
    def _parse_devices(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Parse the router's device response."""
        devices_dict: dict[str, dict[str, Any]] = {}
        info_array = data.get("resp_body", {}).get("info_array", [])
        
        for bridge in info_array:
            for port_group in bridge.get("devices", []):
                port_name = port_group.get("port")
                for device in port_group.get("device_list", []):
                    mac = device.get("mac_addr")
                    if mac:
                        normalized_mac = format_mac(mac)
                        devices_dict[normalized_mac] = {
                            "hostname": device.get("hostname"),
                            "ipv4_address": device.get("ipv4_addr"),
                            "port": port_name,
                            "dhcp": device.get("dhcp"),
                        }
        
        return devices_dict
