"""Sensor for my first"""
import datetime
import logging
from datetime import timedelta

try:
    import homeassistant.helpers.config_validation as cv
    import voluptuous as vol
    from homeassistant.helpers.update_coordinator import (
        CoordinatorEntity,
        DataUpdateCoordinator,
    )
    from homeassistant.core import HomeAssistant
    from homeassistant.components.sensor import PLATFORM_SCHEMA
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import callback
    from homeassistant.helpers.restore_state import RestoreEntity
    from homeassistant.helpers.typing import HomeAssistantType
    from homeassistant.util import Throttle
    from homeassistant.const import (
        ATTR_ATTRIBUTION,
    )

except ImportError:
    # si py test
    pass


from .const import (
    DOMAIN,
    __VERSION__,
    __name__,
    _consommation,
    _production,
    SENSOR_TYPES,
    COORDINATOR_ENEDIS,
    ENTITY_DELAI,
)

_LOGGER = logging.getLogger(__name__)
from .sensorEnedis import manageSensorState

ICON = "mdi:package-variant-closed"


class myEnedisSensorYesterdayCostCoordinator(CoordinatorEntity, RestoreEntity):
    """."""

    def __init__(
        self, sensor_type, coordinator: DataUpdateCoordinator, typeSensor=_consommation
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._myDataSensorEnedis = manageSensorState()
        self._myDataSensorEnedis.init(coordinator.clientEnedis, _LOGGER, __VERSION__)
        interval = sensor_type[ENTITY_DELAI]
        self.update = Throttle(timedelta(seconds=interval))(self._update)
        self._attributes = {}
        self._state = None
        self._unit = "€"
        self._lastState = None
        self._lastAttributes = None
        self._typeSensor = typeSensor
        self._lastYesterday = None

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        if self._typeSensor == _production:
            name = "myEnedis.cost.yesterday.%s.production" % (
                self._myDataSensorEnedis.get_PDL_ID()
            )
        else:
            name = "myEnedis.cost.yesterday.%s" % (
                self._myDataSensorEnedis.get_PDL_ID()
            )
        return name

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._typeSensor == _production:
            name = "myEnedis.cost.yesterday.%s.production" % (
                self._myDataSensorEnedis.get_PDL_ID()
            )
        else:
            name = "myEnedis.cost.yesterday.%s" % (
                self._myDataSensorEnedis.get_PDL_ID()
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
