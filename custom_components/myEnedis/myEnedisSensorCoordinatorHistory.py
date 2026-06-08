"""Sensor history for myEnedis."""
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


class myEnedisSensorCoordinatorHistory(BaseEnedisCoordinatorEntity):
    def __init__(
        self,
        sensor_type: dict[str, int | str],
        coordinator: DataUpdateCoordinator,
        typeSensor=_consommation,
        detail="",
    ):
        super().__init__(coordinator, "kWh", typeSensor)
        self._detail = detail

    @property
    def unique_id(self):
        return f"{self._myDataSensorEnedis.get_PDL_ID()}_history_{self._detail}".lower()

    @property
    def name(self):
        if self._typeSensor == _production:
            return f"myEnedis.history.{self._myDataSensorEnedis.get_PDL_ID()}.production.{self._detail}"
        return f"myEnedis.history.{self._myDataSensorEnedis.get_PDL_ID()}.{self._detail}"

    def _update_state(self):
        self._attributes = {ATTR_ATTRIBUTION: ""}
        laDate = datetime.datetime.today() - datetime.timedelta(2)
        status_counts, state = self._myDataSensorEnedis.getStatusHistory(
            laDate, self._detail
        )
        status_counts["lastUpdate"] = datetime.datetime.today().strftime("%Y-%m-%d %H:%M")
        self._attributes.update(status_counts)
        self._state = state
