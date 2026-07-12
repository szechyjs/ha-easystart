"""The EasyStart integration"""

import logging

from bleak.backends.device import BLEDevice
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

type EasyStartConfigEntry = ConfigEntry[EasyStartDataUpdateCoordinator]


class EasyStartDataUpdateCoordinator(DataUpdateCoordinator[Foo]):
    """Class to manage fetching EasyStart data."""

    ble_device: BLEDevice
    config_entry: EasyStartConfigEntry
