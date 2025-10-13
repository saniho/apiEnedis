"""Sensor for my first"""
from __future__ import annotations

import datetime
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


from .const import __VERSION__, ENTITY_DELAI, __name__, _consommation, _production
from .sensorEnedis import manageSensorState

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:package-variant-closed"


class myEnedisSensorCoordinatorHistory(CoordinatorEntity, RestoreEntity):
    """."""

    def __init__(
        self,
        sensor_type: dict[str, int | str],
        coordinator: DataUpdateCoordinator,
        typeSensor=_consommation,
        detail="",
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._myDataSensorEnedis = manageSensorState()
        self._myDataSensorEnedis.init(coordinator.clientEnedis, _LOGGER, __VERSION__)
        # ajout interval dans le sensor
        # Assure que la valeur est un float:
        try:
            interval = float(sensor_type[ENTITY_DELAI])
        except:
            interval = 60.0
            _LOGGER.warn(f"{ENTITY_DELAI} non defini pour le sensor")
        self.update = Throttle(timedelta(seconds=interval))(self._update)
        _LOGGER.info("frequence mise à jour en seconde : %s", (interval))
        self._attributes: dict[str, int | str] = {}
        self._state: str
        self._unit = "kWh"
        self._lastState = None
        self._lastAttributes = None
        self._typeSensor = typeSensor
        self._detail = detail

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        name = f"{self._myDataSensorEnedis.get_PDL_ID()}_history_{self._detail}".lower()
        return name

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._typeSensor == _production:
            name = "myEnedis.history.{}.production.{}".format(
                self._myDataSensorEnedis.get_PDL_ID(),
                self._detail,
            )
        else:
            name = "myEnedis.history.{}.{}".format(
                self._myDataSensorEnedis.get_PDL_ID(),
                self._detail,
            )
        return name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state

        @callback
        def update():
            """Update state."""
            self._update_state()
            self.async_write_ha_state()

        self.async_on_remove(self.coordinator.async_add_listener(update))
        self._update_state()
        if not state:
            return

    def _update_state(self):
        """Update sensors state."""
        self._attributes = {
            ATTR_ATTRIBUTION: "",
        }
        laDate = datetime.datetime.today() - datetime.timedelta(2)
        # on fait 2 jours, car les données de la veille ne sont pas encore disponible
        status_counts, state = self._myDataSensorEnedis.getStatusHistory(
            laDate, self._detail
        )
        status_counts["lastUpdate"] = datetime.datetime.today().strftime(
            "%Y-%m-%d %H:%M"
        )
        self._attributes.update(status_counts)
        self._state = state

    def _update(self):
        """Update device state."""
        self._attributes = {ATTR_ATTRIBUTION: ""}
        self._state = "unavailable"
        # self._update_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
