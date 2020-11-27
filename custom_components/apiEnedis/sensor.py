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

__VERSION__ = "1.0.3.2"

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
            try:
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

                last7daysHP = self._myDataEnedis.get7DaysHP()
                listeClef = list(last7daysHP.keys())
                listeClef.reverse()
                niemejour = 0
                for clef in listeClef:
                    niemejour += 1
                    status_counts['day_%s_HP' % (niemejour)] = last7daysHP[clef]
                last7daysHC = self._myDataEnedis.get7DaysHC()
                listeClef = list(last7daysHP.keys())
                listeClef.reverse()
                niemejour = 0
                for clef in listeClef:
                    #print(clef, " ", last7daysHC[clef])
                    niemejour += 1
                    status_counts['day_%s_HC' % (niemejour)] = last7daysHC[clef]
                # gestion du cout par jour ....

                niemejour = 0
                cout = []
                for clef in listeClef:
                    niemejour += 1
                    cout.append( 0.001 * self._myDataEnedis.getHCCost( last7daysHC[clef] ) +
                                 0.001 * self._myDataEnedis.getHPCost( last7daysHP[clef] ) )
                status_counts['dailyweek_cost'] = [(day_cost) for day_cost in cout]
                niemejour = 0
                coutHC = []
                for clef in listeClef:
                    niemejour += 1
                    coutHC.append(
                        0.001 * self._myDataEnedis.getHCCost(last7daysHC[clef]))
                status_counts['dailyweek_costHC'] = [(day_cost) for day_cost in coutHC]

                niemejour = 0
                dailyHC = []
                for clef in listeClef:
                    niemejour += 1
                    dailyHC.append(last7daysHC[clef])
                status_counts['dailyweek_HC'] = [(0.001 * day_HC) for day_HC in dailyHC]

                status_counts['dailyweek'] = [(day) for day in listeClef]
                niemejour = 0
                coutHP = []
                for clef in listeClef:
                    niemejour += 1
                    coutHP.append(
                        0.001 * self._myDataEnedis.getHPCost(last7daysHP[clef]))
                status_counts['dailyweek_costHP'] = [(day_cost) for day_cost in coutHP]

                niemejour = 0
                dailyHP = []
                for clef in listeClef:
                    niemejour += 1
                    dailyHP.append(last7daysHP[clef])
                status_counts['dailyweek_HP'] = [(0.001 * day_HP) for day_HP in dailyHP]

                status_counts["halfhourly"] = []
                status_counts["offpeak_hours"] = self._myDataEnedis.getYesterdayHC() * 0.001
                status_counts["peak_hours"] = self._myDataEnedis.getYesterdayHP() * 0.001
                if (( self._myDataEnedis.getYesterdayHC() + self._myDataEnedis.getYesterdayHP() ) != 0 ):
                    status_counts["peak_offpeak_percent"] = ( self._myDataEnedis.getYesterdayHP()* 100 )/ \
                    ( self._myDataEnedis.getYesterdayHC() + self._myDataEnedis.getYesterdayHP() )
                else:
                    status_counts["peak_offpeak_percent"] = 0
                status_counts["yesterday_HC_cost"] = 0.001 * self._myDataEnedis.getHCCost( self._myDataEnedis.getYesterdayHC())
                status_counts["yesterday_HP_cost"] = 0.001 * self._myDataEnedis.getHPCost( self._myDataEnedis.getYesterdayHP())
                status_counts["daily_cost"] = status_counts["yesterday_HC_cost"] + status_counts["yesterday_HP_cost"]
                status_counts['current_week'] = self._myDataEnedis.getCurrentWeek() * 0.001
                status_counts['last_month'] = self._myDataEnedis.getLastMonth() * 0.001
                status_counts['current_month'] = self._myDataEnedis.getCurrentMonth() * 0.001
                status_counts['last_year'] = self._myDataEnedis.getLastYear() * 0.001
                status_counts['current_year'] = self._myDataEnedis.getCurrentYear() * 0.001
                status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
                if (( self._myDataEnedis.getLastMonthLastYear() != None) and
                        (self._myDataEnedis.getLastMonthLastYear() != 0) and
                        (self._myDataEnedis.getLastMonth() != None)):
                    status_counts["monthly_evolution"] = \
                        (( self._myDataEnedis.getLastMonth() - self._myDataEnedis.getLastMonthLastYear())
                        / self._myDataEnedis.getLastMonthLastYear() ) *100
                else:
                    status_counts["monthly_evolution"] = 0
                status_counts["subscribed_power"] = self._myDataEnedis.getsubscribed_power()
                status_counts["offpeak_hours_information"] = self._myDataEnedis.getoffpeak_hours()
                #status_counts['yesterday'] = ""
                self._attributes = {ATTR_ATTRIBUTION: ""}
                self._attributes.update(status_counts)
                ## pour debloquer
                self._state = status_counts['yesterday']*0.001
            except:
                self._attributes = {ATTR_ATTRIBUTION: ""}
                status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
                self._attributes.update(status_counts)
        else:
            return

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
