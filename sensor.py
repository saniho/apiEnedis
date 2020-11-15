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

__VERSION__ = "1.0.1.2"

SCAN_INTERVAL = timedelta(seconds=1800)# interrogation enedis ?
DEFAUT_DELAI_INTERVAL = 3600 # interrogation faite toutes 2 les heures

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_CODE): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_DELAY, default=DEFAUT_DELAI_INTERVAL): cv.positive_int,
    }
)

from . import apiEnedis


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the platform."""
    _LOGGER.warning("myEnedis version %s " %( __VERSION__))
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    code = config.get(CONF_CODE)
    update_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    delai_interval = config.get(CONF_DELAY)

    try:
        session = []
    except :
        _LOGGER.exception("Could not run my First Extension")
        return False
    #_LOGGER.warning("passe ici %s %s " %( token, code ))
    myDataEnedis = apiEnedis.apiEnedis( token, code, delai_interval, _LOGGER )
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
        self.update = Throttle(interval)(self._update)

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myEnedis"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return ""

    def _update(self):
        """Update device state."""
        import datetime
        status_counts = defaultdict(int)

        _LOGGER.warning("call update")
        # gestion du None et du non update des valeurs precedentes
        self._myDataEnedis.update()
        if ( self._myDataEnedis.getStatusLastCall()):# update avec statut ok
            status_counts["lastSynchro"] = datetime.datetime.now()
            status_counts["lastUpdate"] = self._myDataEnedis.getLastUpdate()
            status_counts["timeLastCall"] = self._myDataEnedis.getTimeLastCall()
            status_counts['yesterday'] = self._myDataEnedis.getYesterday()
            status_counts['last_week'] = self._myDataEnedis.getLastWeek()
            status_counts['current_week'] = self._myDataEnedis.getCurrentWeek()
            status_counts['last_month'] = self._myDataEnedis.getLastMonth()
            status_counts['current_month'] = self._myDataEnedis.getCurrentMonth()
            status_counts['last_year'] = self._myDataEnedis.getLastYear()
            status_counts['current_year'] = self._myDataEnedis.getCurrentYear()
            status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
            #status_counts['yesterday'] = ""
            self._attributes = {ATTR_ATTRIBUTION: ""}
            self._attributes.update(status_counts)
            ## pour debloquer
            self._state = status_counts['yesterday']
        else:
            return

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
