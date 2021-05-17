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
    __VERSION__,
    __name__,
    _consommation,
    _production,
    SENSOR_TYPES,
    COORDINATOR_ENEDIS,
    CONF_TOKEN,
    CONF_CODE,
    HC_COST,
    HP_COST,
    HEURESCREUSES_ON,
    HEURES_CREUSES,
)
_LOGGER = logging.getLogger(__name__)
from .sensorEnedis import manageSensorState

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA

# pour gerer les anciennes config via yaml et le message d'ereur
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
                vol.Required(CONF_TOKEN): cv.string,
                vol.Required(CONF_CODE): cv.string,
                vol.Optional(HC_COST,default="0.0"): cv.string,
                vol.Optional(HP_COST,default="0.0"): cv.string,
                vol.Optional(HEURESCREUSES_ON,default=True): cv.boolean,
                vol.Optional(HEURES_CREUSES,default="[]"): cv.string,
            })

ICON = "mdi:package-variant-closed"

from .myEnedisSensorCoordinator import myEnedisSensorCoordinator
from .myEnedisSensorCoordinatorHistory import myEnedisSensorCoordinatorHistory
from .myEnedisSensorYesterdayCostCoordinator import myEnedisSensorYesterdayCostCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the MyEnedis sensor platform."""
    coordinator_enedis = hass.data[DOMAIN][entry.entry_id][COORDINATOR_ENEDIS]

    entities = []
    for sensor_type in SENSOR_TYPES:
        mysensor = SENSOR_TYPES[sensor_type]
        if sensor_type == "principal":
            entities.append(myEnedisSensorCoordinator(mysensor, coordinator_enedis))
        elif sensor_type == "history_all":
            entities.append(myEnedisSensorCoordinatorHistory(mysensor, coordinator_enedis, detail="ALL"))
        elif sensor_type == "history_hc":
            entities.append(myEnedisSensorCoordinatorHistory(mysensor, coordinator_enedis, detail="HC"))
        elif sensor_type == "history_hp":
            entities.append(myEnedisSensorCoordinatorHistory(mysensor, coordinator_enedis, detail="HP"))
        elif sensor_type == "yesterdayCost":
            entities.append(myEnedisSensorYesterdayCostCoordinator(mysensor, coordinator_enedis))
        else:
            pass
            #entities.append(MeteoFranceSensor(sensor_type, coordinator_enedis))

    async_add_entities(
        entities,
        False,
    )
