"""Coordinator for the EasyStart integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import override

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import (
    close_stale_connections_by_address,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    MIN_PACKET_LENGTH,
    NOTIFY_CHARACTERISTIC_UUID,
    NOTIFY_TIMEOUT,
    READ_LIVE_COMMAND,
    SCAN_INTERVAL,
    STATUS_STRINGS,
    VOLTAGE,
    WRITE_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)

type EasyStartConfigEntry = ConfigEntry[EasyStartDataUpdateCoordinator]


@dataclass
class EasyStartData:
    """Parsed data from a single EasyStart BLE notification."""

    live_current: float
    live_power: float
    line_frequency: float
    last_start_peak: float
    scpt_delay: int
    total_faults: int
    total_starts: int
    status: str


def _parse_packet(data: bytearray) -> EasyStartData:
    """Parse an 18-byte EasyStart notify packet into an EasyStartData instance."""
    if len(data) < MIN_PACKET_LENGTH:
        raise ValueError(
            f"Packet too short: expected >={MIN_PACKET_LENGTH} bytes, got {len(data)}"
        )

    factor = 256.0

    live_current = ((data[4] & 0xFF) + ((data[5] & 0xFF) * factor)) / 10.0
    line_frequency = 500000.0 / ((data[6] & 0xFF) + ((data[7] & 0xFF) * factor))
    last_start_peak = ((data[8] & 0xFF) + ((data[9] & 0xFF) * factor)) / 10.0
    scpt_delay = (data[10] & 0xFF) + ((data[11] & 0xFF) * 256)
    total_faults = (data[12] & 0xFF) + ((data[13] & 0xFF) * 256)
    total_starts = data[14] + (data[15] << 8) + (data[16] << 16) + (data[17] << 24)

    status_index = data[2] & 0xFF
    status = (
        STATUS_STRINGS[status_index]
        if status_index < len(STATUS_STRINGS)
        else "Unknown"
    )

    return EasyStartData(
        live_current=live_current,
        live_power=live_current * VOLTAGE,
        line_frequency=line_frequency,
        last_start_peak=last_start_peak,
        scpt_delay=scpt_delay,
        total_faults=total_faults,
        total_starts=total_starts,
        status=status,
    )


class EasyStartDataUpdateCoordinator(DataUpdateCoordinator[EasyStartData]):
    """Coordinator that polls an EasyStart device over BLE."""

    ble_device: BLEDevice
    config_entry: EasyStartConfigEntry

    def __init__(self, hass: HomeAssistant, entry: EasyStartConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    @override
    async def _async_setup(self) -> None:
        """Resolve the BLEDevice and close any stale connections."""
        address = self.config_entry.unique_id
        assert address is not None

        await close_stale_connections_by_address(address)

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, address, connectable=True
        )
        if not ble_device:
            raise ConfigEntryNotReady(
                f"EasyStart device {address} not found. "
                "Make sure the device is powered on and within Bluetooth range."
            )
        self.ble_device = ble_device

    @override
    async def _async_update_data(self) -> EasyStartData:
        """Connect to the device, request live data, and parse the response."""
        address = self.config_entry.unique_id
        assert address is not None

        # Re-resolve the BLEDevice on each poll; the underlying adapter path can
        # change between updates as Home Assistant rotates through adapters.
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, address, connectable=True
        )
        if ble_device:
            self.ble_device = ble_device

        notification_event = asyncio.Event()
        received_data: bytearray | None = None

        def handle_notification(
            _characteristic: BleakGATTCharacteristic, data: bytearray
        ) -> None:
            nonlocal received_data
            # Ignore success-response packets (ASCII `{...}` containing "Success")
            try:
                if b"Success" in bytes(data):
                    return
            except Exception:  # noqa: BLE001
                pass
            received_data = data
            notification_event.set()

        try:
            client: BleakClient = await establish_connection(
                BleakClient,
                self.ble_device,
                self.ble_device.address,
            )
        except Exception as err:
            raise UpdateFailed(f"Could not connect to EasyStart device: {err}") from err

        try:
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handle_notification)
            await client.write_gatt_char(
                WRITE_CHARACTERISTIC_UUID,
                READ_LIVE_COMMAND,
                response=False,
            )

            try:
                await asyncio.wait_for(
                    notification_event.wait(), timeout=NOTIFY_TIMEOUT
                )
            except TimeoutError as err:
                raise UpdateFailed(
                    "Timed out waiting for EasyStart notification"
                ) from err

            if received_data is None:
                raise UpdateFailed("No data received from EasyStart device")

            try:
                return _parse_packet(received_data)
            except ValueError as err:
                raise UpdateFailed(f"Failed to parse EasyStart packet: {err}") from err

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with EasyStart device: {err}"
            ) from err
        finally:
            await client.disconnect()
