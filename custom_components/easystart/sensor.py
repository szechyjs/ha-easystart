"""Support for EasyStart BLE sensors."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import (
    EasyStartConfigEntry,
    EasyStartData,
    EasyStartDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EasyStartSensorEntityDescription(SensorEntityDescription):
    """Describes an EasyStart sensor."""


SENSOR_DESCRIPTIONS: tuple[EasyStartSensorEntityDescription, ...] = (
    EasyStartSensorEntityDescription(
        key="live_current",
        translation_key="live_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    EasyStartSensorEntityDescription(
        key="live_power",
        translation_key="live_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    EasyStartSensorEntityDescription(
        key="line_frequency",
        translation_key="line_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    EasyStartSensorEntityDescription(
        key="last_start_peak",
        translation_key="last_start_peak",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    EasyStartSensorEntityDescription(
        key="scpt_delay",
        translation_key="scpt_delay",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EasyStartSensorEntityDescription(
        key="total_faults",
        translation_key="total_faults",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EasyStartSensorEntityDescription(
        key="total_starts",
        translation_key="total_starts",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    EasyStartSensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "normal",
            "unexpected_curr_flt",
            "short_cycle_delay",
            "pwr_intrrptn_fault",
            "stall_fault",
            "stuck_sr_fault",
            "open_ovrld_fault",
            "overcurrent_fault",
            "bad_wiring_fault",
            "wrong_voltage_flt",
            "unknown",
        ],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EasyStartConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up EasyStart sensors from a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        EasyStartSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class EasyStartSensor(CoordinatorEntity[EasyStartDataUpdateCoordinator], SensorEntity):
    """Representation of an EasyStart sensor."""

    _attr_has_entity_name = True
    entity_description: EasyStartSensorEntityDescription

    def __init__(
        self,
        coordinator: EasyStartDataUpdateCoordinator,
        description: EasyStartSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description

        address = coordinator.config_entry.unique_id
        assert address is not None

        self._attr_unique_id = f"{address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, address)},
            name="EasyStart",
            manufacturer="Micro-Air",
            model="EasyStart",
        )

    @property
    @override
    def native_value(self) -> str | float | int | None:
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        data: EasyStartData = self.coordinator.data
        raw = getattr(data, self.entity_description.key)

        if self.entity_description.key == "status":
            return _status_to_option(raw)

        return raw


def _status_to_option(status: str) -> str:
    """Convert a STATUS_STRINGS value to the lowercase underscore option key."""
    return status.lower().replace(" ", "_")
