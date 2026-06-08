"""Sensor Tempo for myEnedis."""
from __future__ import annotations

import logging

try:
    from homeassistant.const import ATTR_ATTRIBUTION
except ImportError:
    pass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base_enedis_coordinator import BaseEnedisCoordinatorEntity

_LOGGER = logging.getLogger(__name__)


class myEnedisSensorCoordinatorTempo(BaseEnedisCoordinatorEntity):
    def __init__(
        self,
        sensor_type,
        coordinator: DataUpdateCoordinator,
    ):
        super().__init__(coordinator, "", None)

    @property
    def unique_id(self):
        return f"myEnedis.{self._myDataSensorEnedis.get_PDL_ID()}.Tempo"

    @property
    def name(self):
        return self.unique_id

    def _update_state(self):
        self._attributes = {ATTR_ATTRIBUTION: ""}
        status_counts, state = self._myDataSensorEnedis.getStatusTempo()
        self._attributes.update(status_counts)
        self._state = state
