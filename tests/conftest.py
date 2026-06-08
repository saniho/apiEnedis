"""HA module stubs for testing without homeassistant installed."""
import sys
from unittest.mock import MagicMock


class _StubEntity:
    pass


class _StubCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def async_added_to_hass(self):
        pass

    async def async_get_last_state(self):
        return None

    def async_write_ha_state(self):
        pass

    def async_on_remove(self, _callback):
        pass


class _StubRestoreEntity:
    async def async_get_last_state(self):
        return None


class _StubSensorEntity:
    pass


class _StubDataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.clientEnedis = None

    def async_add_listener(self, callback):
        return lambda: None

    async def async_request_refresh(self):
        pass

    async def async_config_entry_first_refresh(self):
        pass

    @property
    def data(self):
        return None

    @property
    def last_update_success(self):
        return True


_modules = {
    "homeassistant": MagicMock(),
    "homeassistant.const": MagicMock(),
    "homeassistant.core": MagicMock(),
    "homeassistant.util": MagicMock(),
    "homeassistant.components": MagicMock(),
    "homeassistant.config_entries": MagicMock(),
    "homeassistant.exceptions": MagicMock(),
    "homeassistant.helpers": MagicMock(),
    "homeassistant.helpers.typing": MagicMock(),
    "homeassistant.helpers.config_validation": MagicMock(),
    "homeassistant.helpers.restore_state": type(
        "restore_state", (), {"RestoreEntity": _StubRestoreEntity}
    ),
    "homeassistant.helpers.update_coordinator": type(
        "update_coordinator",
        (),
        {
            "CoordinatorEntity": _StubCoordinatorEntity,
            "DataUpdateCoordinator": _StubDataUpdateCoordinator,
        },
    ),
    "homeassistant.components.sensor": type(
        "sensor",
        (),
        {"SensorEntity": _StubSensorEntity},
    ),
}
for k, v in _modules.items():
    sys.modules[k] = v
