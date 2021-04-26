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
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from homeassistant.util import Throttle
    from homeassistant.const import (
        ATTR_ATTRIBUTION,
    )

except ImportError:
    # si py test
    pass


from .const import (
    DOMAIN,
    __name__,
    _consommation,
    _production,
    SENSOR_TYPES,
    COORDINATOR_ENEDIS,
)
_LOGGER = logging.getLogger(__name__)
from .sensorEnedis import manageSensorState

ICON = "mdi:package-variant-closed"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the MyEnedis sensor platform."""
    coordinator_enedis = hass.data[DOMAIN][entry.entry_id][COORDINATOR_ENEDIS]

    entities = []
    for sensor_type in SENSOR_TYPES:
        if sensor_type == "principal":
            entities.append(myEnedisSensorCoordinator(sensor_type, coordinator_enedis))
        else:
            pass
            #entities.append(MeteoFranceSensor(sensor_type, coordinator_enedis))

    async_add_entities(
        entities,
        False,
    )

class myEnedisSensorCoordinator(CoordinatorEntity, RestoreEntity):
    """."""

    def __init__(self, sensor_type: str, coordinator: DataUpdateCoordinator, typeSensor = _consommation):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._myDataSensorEnedis = manageSensorState()
        self._myDataSensorEnedis.init(coordinator.clientEnedis, _LOGGER)
        self._attributes = {}
        self._state = None
        self._unit = "kWh"
        self._lastState = None
        self._lastAttributes = None
        self._typeSensor = typeSensor

    @property
    def unique_id(self):
        "Return a unique_id for this entity."
        if self._typeSensor == _production:
            name = "myEnedis.%s.production" %(self._myDataSensorEnedis.get_PDL_ID())
        else:
            name = "myEnedis.%s" %(self._myDataSensorEnedis.get_PDL_ID())
        return name

    @property
    def name(self):
        """Return the name of the sensor."""
        if ( self._typeSensor == _production):
            name = "myEnedis.%s.production" %(self._myDataSensorEnedis.get_PDL_ID())
        else:
            name = "myEnedis.%s" %(self._myDataSensorEnedis.get_PDL_ID())
        return name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        self._attributes = {
            ATTR_ATTRIBUTION: "",
        }
        status_counts, state = self._myDataSensorEnedis.getStatus( self._typeSensor )
        self._attributes.update(status_counts)
        self._state = state
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
