"""Sensor for my first"""
import logging

try:
    import homeassistant.helpers.config_validation as cv
    import voluptuous as vol
    from homeassistant.core import HomeAssistant
    from homeassistant.components.sensor import PLATFORM_SCHEMA
    from homeassistant.config_entries import ConfigEntry

except ImportError:
    # si py test
    pass


from .const import (  # isort:skip
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

# pour gerer les anciennes config via yaml et le message d'ereur
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_CODE): cv.string,
        vol.Optional(HC_COST, default="0.0"): cv.string,
        vol.Optional(HP_COST, default="0.0"): cv.string,
        vol.Optional(HEURESCREUSES_ON, default=True): cv.boolean,
        vol.Optional(HEURES_CREUSES, default="[]"): cv.string,
    }
)

ICON = "mdi:package-variant-closed"

from .myEnedisSensorCoordinator import myEnedisSensorCoordinator
from .myEnedisSensorCoordinatorHistory import myEnedisSensorCoordinatorHistory
from .myEnedisSensorYesterdayCostCoordinator import (
    myEnedisSensorYesterdayCostCoordinator,
)
from .myEnedisSensorCoordinatorEnergy import myEnedisSensorCoordinatorEnergy
from .myEnedisSensorCoordinatorEnergyDetailHours import (
    myEnedisSensorCoordinatorEnergyDetailHours,
)
from .myEnedisSensorCoordinatorEnergyDetailHoursCost import (
    myEnedisSensorCoordinatorEnergyDetailHoursCost,
)


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
            entities.append(
                myEnedisSensorCoordinatorHistory(
                    mysensor, coordinator_enedis, detail="ALL"
                )
            )
        elif sensor_type == "history_hc":
            entities.append(
                myEnedisSensorCoordinatorHistory(
                    mysensor, coordinator_enedis, detail="HC"
                )
            )
        elif sensor_type == "history_hp":
            entities.append(
                myEnedisSensorCoordinatorHistory(
                    mysensor, coordinator_enedis, detail="HP"
                )
            )
        elif sensor_type == "yesterdayCost":
            entities.append(
                myEnedisSensorYesterdayCostCoordinator(mysensor, coordinator_enedis)
            )
        elif sensor_type == "energy":
            entities.append(
                myEnedisSensorCoordinatorEnergy(mysensor, coordinator_enedis)
            )
        elif sensor_type == "energyDetailHours":
            entities.append(
                myEnedisSensorCoordinatorEnergyDetailHours(mysensor, coordinator_enedis)
            )
        elif sensor_type == "energyDetailHoursCost":
            entities.append(
                myEnedisSensorCoordinatorEnergyDetailHoursCost(
                    mysensor, coordinator_enedis
                )
            )
        else:
            pass

    async_add_entities(
        entities,
        False,
    )
