"""EasyStart integration"""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up EasyStart device from a config entry"""

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry"""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
