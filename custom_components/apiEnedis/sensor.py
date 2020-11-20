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

__VERSION__ = "1.0.2.5"

SCAN_INTERVAL = timedelta(seconds=1800)# interrogation enedis ?
DEFAUT_DELAI_INTERVAL = 3600 # interrogation faite toutes 2 les heures
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
        return "myEnedis"

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
        # gestion du None et du non update des valeurs precedentes
        status_counts["version"] = __VERSION__
        self._myDataEnedis.update()
        if ( self._myDataEnedis.getStatusLastCall()):# update avec statut ok
            status_counts["lastSynchro"] = datetime.datetime.now()
            status_counts["lastUpdate"] = self._myDataEnedis.getLastUpdate()
            status_counts["timeLastCall"] = self._myDataEnedis.getTimeLastCall()
            # à supprimer car doublon avec j_1
            status_counts['yesterday'] = self._myDataEnedis.getYesterday()
            status_counts['last_week'] = self._myDataEnedis.getLastWeek()
            last7days = self._myDataEnedis.getLast7Days()
            for day in last7days:
                status_counts['day_%s' %(day["niemejour"])] = day["value"]
            status_counts['daily'] = [(day["value"]*0.001) for day in last7days]

            status_counts["halfhourly"] = []
            status_counts["offpeak_hours"] = self._myDataEnedis.getYesterdayHC() * 0.001 * 0.5
            status_counts["peak_hours"] = self._myDataEnedis.getYesterdayHP() * 0.001 * 0.5
            if (( self._myDataEnedis.getYesterdayHC() + self._myDataEnedis.getYesterdayHP() ) != 0 ):
                status_counts["peak_offpeak_percent"] = ( self._myDataEnedis.getYesterdayHP()* 100 )/ \
                ( self._myDataEnedis.getYesterdayHC() + self._myDataEnedis.getYesterdayHP() )
            else:
                status_counts["peak_offpeak_percent"] = 0
            status_counts["yesterday_HC_cost"] = 0.001 * self._myDataEnedis.getHCCost( self._myDataEnedis.getYesterdayHC())
            status_counts["yesterday_HP_cost"] = 0.001 * self._myDataEnedis.getHPCost( self._myDataEnedis.getYesterdayHP())
            status_counts["daily_cost"] = status_counts["yesterday_HC_cost"] + status_counts["yesterday_HP_cost"]
            status_counts['current_week'] = self._myDataEnedis.getCurrentWeek()
            status_counts['last_month'] = self._myDataEnedis.getLastMonth()
            status_counts['current_month'] = self._myDataEnedis.getCurrentMonth()
            status_counts['last_year'] = self._myDataEnedis.getLastYear()
            status_counts['current_year'] = self._myDataEnedis.getCurrentYear()
            status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
            if (( self._myDataEnedis.getLastMonthLastYear() != None) and
                    (self._myDataEnedis.getLastMonthLastYear() != 0) and
                    (self._myDataEnedis.getLastMonth() != None)):
                status_counts["monthly_evolution"] = \
                    (( self._myDataEnedis.getLastMonth() - self._myDataEnedis.getLastMonthLastYear())
                    / self._myDataEnedis.getLastMonthLastYear() ) *100
            else:
                status_counts["monthly_evolution"] = 0
            #status_counts['yesterday'] = ""
            self._attributes = {ATTR_ATTRIBUTION: ""}
            self._attributes.update(status_counts)
            ## pour debloquer
            self._state = status_counts['yesterday']*0.001
        else:
            return

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
