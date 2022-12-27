"""Sensor for my first"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

try:
    from homeassistant.const import ATTR_ATTRIBUTION
    from homeassistant.core import callback
    from homeassistant.helpers.restore_state import RestoreEntity
    from homeassistant.helpers.update_coordinator import (
        CoordinatorEntity,
        DataUpdateCoordinator,
    )
    from homeassistant.util import Throttle

except ImportError:
    # si py test
    pass


from .const import __VERSION__, ENTITY_DELAI, __name__
from .sensorEnedis import manageSensorState

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:package-variant-closed"


class myEnedisSensorCoordinatorEcoWatt(CoordinatorEntity, RestoreEntity):
    """."""

    def __init__(
        self,
        sensor_type,
        coordinator: DataUpdateCoordinator,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._myDataSensorEnedis = manageSensorState()
        self._myDataSensorEnedis.init(coordinator.clientEnedis, _LOGGER, __VERSION__)
        interval = sensor_type[ENTITY_DELAI]
        self.update = Throttle(timedelta(seconds=interval))(self._update)
        self._attributes: dict[str, str] = {}
        self._state: str = None
        self._unit = ""
        self._lastState = None
        self._lastAttributes = None

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        name = f"myEnedis.{self._myDataSensorEnedis.get_PDL_ID()}.EcoWatt"
        return name

    @property
    def name(self):
        """Return the name of the sensor."""
        name = f"myEnedis.{self._myDataSensorEnedis.get_PDL_ID()}.EcoWatt"
        return name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    async def _async_update(self):
        """Update state asynchronously"""
        self._update_state()
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state

        # TEST info
        try:
            if "typeCompteur" in state.attributes:
                self.attrs = state.attributes
                _LOGGER.info("Redemarrage avec element present ??")
        except:
            _LOGGER.info("Redemarrage mais rien de present")

        @callback
        def update():
            """Update state."""
            asyncio.create_task(self._async_update())

        self.async_on_remove(self.coordinator.async_add_listener(update))
        asyncio.create_task(self._async_update())

    def _update_state(self):
        """Update sensors state."""
        self._attributes = {
            ATTR_ATTRIBUTION: "",
        }
        status_counts, state = self._myDataSensorEnedis.getStatusEcoWatt()
        self._attributes.update(status_counts)
        self._state = state

    def _update(self):
        """Update device state."""
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._state = "unavailable"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
