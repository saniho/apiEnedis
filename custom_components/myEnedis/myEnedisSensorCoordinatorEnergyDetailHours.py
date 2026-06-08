"""Sensor energy detail hours for myEnedis."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
    from homeassistant.const import ATTR_ATTRIBUTION, UnitOfEnergy
except ImportError:
    pass

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base_enedis_coordinator import BaseEnedisCoordinatorEntity
from .const import _consommation, _production

_LOGGER = logging.getLogger(__name__)


class myEnedisSensorCoordinatorEnergyDetailHours(BaseEnedisCoordinatorEntity):
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
            return f"myEnedis.energy.Hours.{self._myDataSensorEnedis.get_PDL_ID()}.production"
        return f"myEnedis.energy.Hours.{self._myDataSensorEnedis.get_PDL_ID()}"

    @property
    def name(self):
        return self.unique_id

    def _update_state(self):
        self._attributes = {ATTR_ATTRIBUTION: ""}
        _, status_counts, state = self._myDataSensorEnedis.getStatusEnergyDetailHours(self._typeSensor)
        self._state = state

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self):
        return SensorStateClass.TOTAL

    @property
    def native_unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR
