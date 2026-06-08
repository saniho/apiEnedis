"""Sensor yesterday cost for myEnedis."""
from __future__ import annotations

import datetime
import logging

try:
    from homeassistant.const import ATTR_ATTRIBUTION
except ImportError:
    pass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base_enedis_coordinator import BaseEnedisCoordinatorEntity
from .const import _consommation, _production

_LOGGER = logging.getLogger(__name__)


class myEnedisSensorYesterdayCostCoordinator(BaseEnedisCoordinatorEntity):
    def __init__(
        self,
        sensor_type,
        coordinator: DataUpdateCoordinator,
        typeSensor=_consommation,
    ):
        super().__init__(coordinator, "EUR", typeSensor)
        self._lastYesterday = None

    @property
    def unique_id(self):
        if self._typeSensor == _production:
            return f"myEnedis.cost.yesterday.{self._myDataSensorEnedis.get_PDL_ID()}.production"
        return f"myEnedis.cost.yesterday.{self._myDataSensorEnedis.get_PDL_ID()}"

    @property
    def name(self):
        return self.unique_id

    def _update_state(self):
        self._attributes = {ATTR_ATTRIBUTION: ""}
        (
            dataAvailable,
            yesterdayDate,
            status_counts,
            state,
        ) = self._myDataSensorEnedis.getStatusYesterdayCost()
        if dataAvailable:
            if (self._lastYesterday != yesterdayDate) and (yesterdayDate is not None):
                status_counts["timeLastCall"] = datetime.datetime.now()
                self._lastYesterday = yesterdayDate
        self._attributes.update(status_counts)
        self._state = state
