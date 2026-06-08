"""Base class for myEnedis sensor coordinators."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.sensor import SensorEntity
    from homeassistant.const import ATTR_ATTRIBUTION
    from homeassistant.core import callback
    from homeassistant.helpers.restore_state import RestoreEntity
    from homeassistant.helpers.update_coordinator import (
        CoordinatorEntity,
        DataUpdateCoordinator,
    )
except ImportError:
    pass

from .const import __VERSION__, _consommation
from .sensorEnedis import manageSensorState

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:package-variant-closed"


class BaseEnedisCoordinatorEntity(CoordinatorEntity, RestoreEntity, SensorEntity):
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        unit: str = "kWh",
        typeSensor=_consommation,
    ):
        super().__init__(coordinator)
        self._myDataSensorEnedis = manageSensorState()
        self._myDataSensorEnedis.init(coordinator.clientEnedis, _LOGGER, __VERSION__)
        self._attributes: dict[str, str] = {}
        self._state = None
        self._unit = unit
        self._lastState = None
        self._lastAttributes = None
        self._typeSensor = typeSensor

    @property
    def native_value(self):
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state

        try:
            if state and "typeCompteur" in state.attributes:
                self.attrs = state.attributes
                _LOGGER.info("Redemarrage avec element present ??")
        except Exception:
            _LOGGER.info("Redemarrage mais rien de present")

        @callback
        def update():
            self._update_state()
            self.async_write_ha_state()

        self.async_on_remove(self.coordinator.async_add_listener(update))
        self._update_state()

    def _update_state(self):
        raise NotImplementedError

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        return ICON
