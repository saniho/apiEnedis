"""Sensor principal for myEnedis."""
from __future__ import annotations

import logging

try:
    from homeassistant.const import ATTR_ATTRIBUTION
except ImportError:
    pass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base_enedis_coordinator import BaseEnedisCoordinatorEntity
from .const import _consommation, _production

_LOGGER = logging.getLogger(__name__)


class myEnedisSensorCoordinator(BaseEnedisCoordinatorEntity):
    def __init__(
        self,
        sensor_type,
        coordinator: DataUpdateCoordinator,
        typeSensor=_consommation,
    ):
        super().__init__(coordinator, "kWh", typeSensor)

    @property
    def unique_id(self):
        if self._typeSensor == _production:
            return f"myEnedis.{self._myDataSensorEnedis.get_PDL_ID()}.production"
        return f"myEnedis.{self._myDataSensorEnedis.get_PDL_ID()}"

    @property
    def name(self):
        return self.unique_id

    def _update_state(self):
        self._attributes = {ATTR_ATTRIBUTION: ""}
        status_counts, state = self._myDataSensorEnedis.getStatus(self._typeSensor)
        self._attributes.update(status_counts)
        self._state = state
