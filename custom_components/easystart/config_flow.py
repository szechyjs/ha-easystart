"""Config flow for the EasyStart integration."""

from __future__ import annotations

import logging
from typing import Any, override

from habluetooth import BluetoothServiceInfoBleak

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class EasyStartConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EasyStart."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    @override
    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": _device_title(discovery_info)}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a Bluetooth discovery."""
        assert self._discovery_info is not None
        discovery_info = self._discovery_info

        if user_input is not None:
            return self.async_create_entry(
                title=_device_title(discovery_info),
                data={CONF_ADDRESS: discovery_info.address},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": _device_title(discovery_info)},
        )

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step — lets the user pick from discovered devices."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            title = self._discovered_devices.get(address, address)
            return self.async_create_entry(
                title=title,
                data={CONF_ADDRESS: address},
            )

        already_configured = self._async_current_ids()
        self._discovered_devices = {
            info.address: _device_title(info)
            for info in async_discovered_service_info(self.hass, connectable=True)
            if info.address not in already_configured and _is_easystart(info)
        }

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=_address_schema(self._discovered_devices),
        )


def _is_easystart(info: BluetoothServiceInfoBleak) -> bool:
    """Return True if the advertisement looks like an EasyStart device."""
    return SERVICE_UUID in info.service_uuids or (
        info.name is not None and info.name.startswith("EasyStart")
    )


def _device_title(info: BluetoothServiceInfoBleak) -> str:
    """Return a human-readable title for the device."""
    return info.name or info.address


def _address_schema(devices: dict[str, str]):
    """Build a voluptuous schema for the address selector."""
    import voluptuous as vol
    from homeassistant.helpers.selector import (
        SelectOptionDict,
        SelectSelector,
        SelectSelectorConfig,
        SelectSelectorMode,
    )

    return vol.Schema(
        {
            vol.Required(CONF_ADDRESS): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=addr, label=name)
                        for addr, name in devices.items()
                    ],
                    mode=SelectSelectorMode.LIST,
                )
            )
        }
    )
