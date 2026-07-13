"""The EasyStart integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_METHOD, Platform, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_ENERGY_ENTRY_ID, DOMAIN
from .coordinator import EasyStartConfigEntry, EasyStartDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Riemann sum integration component domain
_INTEGRATION_DOMAIN = "integration"


async def async_setup_entry(hass: HomeAssistant, entry: EasyStartConfigEntry) -> bool:
    """Set up EasyStart device from a config entry."""
    coordinator = EasyStartDataUpdateCoordinator(hass, entry)

    # Use async_refresh instead of async_config_entry_first_refresh so that
    # a failure (device offline) does not raise ConfigEntryNotReady and block
    # setup. Sensors will be unavailable until the device comes into range.
    await coordinator.async_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Create the Riemann sum energy helper if it doesn't already exist.
    # We store the created entry's ID in our config entry data so we can
    # remove it cleanly on unload and avoid creating duplicates on restart.
    await _async_ensure_energy_helper(hass, entry)

    return True


async def _async_ensure_energy_helper(
    hass: HomeAssistant, entry: EasyStartConfigEntry
) -> None:
    """Create a Riemann sum helper for live_power → kWh if not already present."""
    if CONF_ENERGY_ENTRY_ID in entry.data:
        # Already created — verify it still exists
        existing_id: str = entry.data[CONF_ENERGY_ENTRY_ID]
        if hass.config_entries.async_get_entry(existing_id):
            return
        # Entry was deleted by the user — remove the stored ID and recreate
        _LOGGER.debug("EasyStart energy helper was removed, recreating")
        hass.config_entries.async_update_entry(
            entry,
            data={k: v for k, v in entry.data.items() if k != CONF_ENERGY_ENTRY_ID},
        )

    address = entry.unique_id
    assert address is not None

    # The live_power entity ID is deterministic from the unique_id pattern
    # set in sensor.py: <address>_live_power → sensor.<slug>_live_power
    # We use the unique_id form so it survives entity renames.
    power_unique_id = f"{address}_live_power"

    # Resolve the current entity_id for the power sensor
    entity_registry = er.async_get(hass)
    power_entity = entity_registry.async_get_entity_id(
        "sensor", DOMAIN, power_unique_id
    )
    if power_entity is None:
        _LOGGER.warning(
            "EasyStart live_power entity not found, skipping energy helper creation"
        )
        return

    _LOGGER.debug("Creating EasyStart energy helper for %s", power_entity)

    result = await hass.config_entries.flow.async_init(
        _INTEGRATION_DOMAIN,
        context={"source": "user"},
    )

    if result.get("type") != "form":
        _LOGGER.warning(
            "Unexpected result starting integration flow: %s", result.get("type")
        )
        return

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            "name": "Energy",
            "source": power_entity,
            CONF_METHOD: "left",
            "round": 2,
            "unit_time": UnitOfTime.HOURS,
            "unit_prefix": "k",
        },
    )

    if result.get("type") == "create_entry":
        new_entry_id: str = result["result"].entry_id
        _LOGGER.debug("Created EasyStart energy helper: %s", new_entry_id)
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_ENERGY_ENTRY_ID: new_entry_id},
        )
    else:
        _LOGGER.warning(
            "Failed to create EasyStart energy helper: %s", result.get("type")
        )


async def async_unload_entry(hass: HomeAssistant, entry: EasyStartConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
