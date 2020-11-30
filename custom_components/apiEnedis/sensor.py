"""Sensor for my first"""
import logging
from collections import defaultdict
from datetime import timedelta

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME,
    CONF_TOKEN,
    CONF_CODE,
    CONF_DELAY,
    CONF_SCAN_INTERVAL,
    ATTR_ATTRIBUTION,
)

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.util import slugify
from homeassistant.util.dt import now, parse_date

_LOGGER = logging.getLogger(__name__)

DOMAIN = "saniho"

ICON = "mdi:package-variant-closed"

__VERSION__ = "1.0.4.0"

SCAN_INTERVAL = timedelta(seconds=1800)# interrogation enedis ?
DEFAUT_DELAI_INTERVAL = 7200 # interrogation faite toutes 2 les heures
DEFAUT_HEURES_CREUSES = "[]"
DEFAUT_COST = "0.0"
HEURES_CREUSES = "heures_creuses"
HC_COUT = "hc_cout"
HP_COUT = "hp_cout"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_CODE): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(HEURES_CREUSES, default=DEFAUT_HEURES_CREUSES): cv.string,
        vol.Optional(CONF_DELAY, default=DEFAUT_DELAI_INTERVAL): cv.positive_int,
        vol.Optional(HC_COUT, default=DEFAUT_COST): cv.string,
        vol.Optional(HP_COUT, default=DEFAUT_COST): cv.string,
    }
)

from . import apiEnedis
from . import sensorEnedis


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    _LOGGER.warning("myEnedis version %s " %( __VERSION__))
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    code = config.get(CONF_CODE)
    #[['00:30', '07:00'], ['10:00', "11:30"]]
    heuresCreusesCh = config.get(HEURES_CREUSES)
    heuresCreuses = eval(heuresCreusesCh)
    HCCost = float(config.get(HC_COUT))
    HPCost = float(config.get(HP_COUT))
    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    delai_interval = config.get(CONF_DELAY)

    try:
        session = []
    except :
        _LOGGER.exception("Could not run my First Extension")
        return False
    #_LOGGER.warning("passe ici %s %s " %( token, code ))
    myDataEnedis = apiEnedis.apiEnedis( token, code, delai_interval, \
        heuresCreuses=heuresCreuses, heuresCreusesCost=HCCost, heuresPleinesCost=HPCost, log=_LOGGER )
    myDataEnedis.updateContract()
    myDataEnedis.updateHCHP()
    _LOGGER.warning("myDataEnedis._heuresCreuses: %s" %(myDataEnedis._heuresCreuses))
    add_entities([myEnedis(session, name, update_interval, myDataEnedis )], True)
    # on va gerer  un element par heure ... maintenant

class myEnedis(Entity):
    """."""

    def __init__(self, session, name, interval, myDataEnedis):
        """Initialize the sensor."""
        self._session = session
        self._name = name
        self._myDataEnedis = myDataEnedis
        self._attributes = None
        self._state = None
        self._unit = "kWh"
        self.update = Throttle(interval)(self._update)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myEnedis.%s" %(self._myDataEnedis.get_PDL_ID())
        #return "myEnedis"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    def _update(self):
        """Update device state."""
        import datetime
        status_counts = defaultdict(int)

        _LOGGER.warning("call update")
        try:
            status_counts = sensorEnedis.manageSensorState(self._myDataEnedis)
            if (self._myDataEnedis.getStatusLastCall() == False):
                _LOGGER.warning("%s - **** ERROR *** %s" %(self.get_PDL_ID(), self._myDataEnedis.getLastMethodCall()))
                self._myDataEnedis.updateLastMethodCallError(self._myDataEnedis.getLastMethodCall())  # on met l'etat precedent
                time.sleep( 10 )
                # si pas ok, alors on fait un deuxième essai
                _LOGGER.warning("%s - **** on va tenter un deuxème essai *** %s" %(self.get_PDL_ID()))
                status_counts = sensorEnedis.manageSensorState(self._myDataEnedis, _LOGGER)
                if (self._myDataEnedis.getStatusLastCall() == False):
                    _LOGGER.warning("%s - **** ERROR *** %s" %(self.get_PDL_ID(), self._myDataEnedis.getLastMethodCall()))
                    self._myDataEnedis.updateLastMethodCallError(self._myDataEnedis.getLastMethodCall())  # on met l'etat precedent
            else:
                self._attributes = {ATTR_ATTRIBUTION: ""}
                self._attributes.update(status_counts)
                self._state = status_counts['yesterday']*0.001
        except:
            self._attributes = {ATTR_ATTRIBUTION: ""}
            status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
            self._attributes.update(status_counts)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
