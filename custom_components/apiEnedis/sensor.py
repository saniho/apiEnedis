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

#from homeassistant.helpers.entity import Entity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import Throttle
from homeassistant.util import slugify
from homeassistant.util.dt import now, parse_date

import time

_LOGGER = logging.getLogger(__name__)

DOMAIN = "saniho"

ICON = "mdi:package-variant-closed"

__VERSION__ = "1.0.5.4"

SCAN_INTERVAL = timedelta(seconds=1800)# interrogation enedis ?
DEFAUT_DELAI_INTERVAL = 7200 # interrogation faite toutes 2 les heures
#DEFAUT_DELAI_INTERVAL = 120 # interrogation faite toutes 2 les heures
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
    _LOGGER.info("myEnedis version %s " %( __VERSION__))
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
    #myDataEnedis.updateContract()
    #myDataEnedis.updateHCHP()
    #_LOGGER.warning("myDataEnedis._heuresCreuses: %s" %(myDataEnedis._heuresCreuses))
    add_entities([myEnedis(session, name, update_interval, myDataEnedis )], True)
    # on va gerer  un element par heure ... maintenant

class myEnedis(RestoreEntity):
    """."""

    def __init__(self, session, name, interval, myDataEnedis):
        """Initialize the sensor."""
        self._session = session
        self._name = name
        self._myDataEnedis = myDataEnedis
        self._attributes = {}
        self._state = None
        self._unit = "kWh"
        self.update = Throttle(interval)(self._update)
        self._lastState = None
        self._lastAttributes = None

    def setLastState(self):
        self._lastState = self._state
    def setLastAttributes(self):
        self._lastAttributes = self._attributes.copy()

    def setStateFromLastState(self):
        if ( self._lastState != None ) :
            self._state = self._lastState
    def setAttributesFromLastAttributes(self):
        if ( self._lastAttributes != None ) :
            self._attributes = self._lastAttributes.copy()
            return self._attributes
        else:
            return {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return "myEnedis.%s" %(self._myDataEnedis.get_PDL_ID())

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

        _LOGGER.info("call update")
        if ( self._myDataEnedis.getContract() == None ):
            try:
                self._myDataEnedis.updateContract()
                self._myDataEnedis.updateHCHP()
            except Exception as inst:
                self._attributes = {ATTR_ATTRIBUTION: ""}
                # on met les anciens attributs
                self.setStateFromLastState()
                self.setAttributesFromLastAttributes()
                if ( inst.args[:2] == ("call", "error")): # gestion que c'est pas une erreur de contrat trop recent ?
                    _LOGGER.warning("Erreur call ERROR %s" %(inst))
                    status_counts['errorLastCall'] = "erreur gateway : %s" %(inst.args[2])
                else:
                    status_counts['errorLastCall'] = "erreur inconnue"
                self._attributes.update(status_counts)
        # mise à jour du contrat

        if ( self._myDataEnedis.getContract() != None ):
            try:
                status_counts = sensorEnedis.manageSensorState(self._myDataEnedis, _LOGGER, __VERSION__)
                if (self._myDataEnedis.getStatusLastCall() == False):
                    _LOGGER.warning("%s - **** ERROR *** %s" %(self._myDataEnedis.get_PDL_ID(), self._myDataEnedis.getLastMethodCall()))
                    self._myDataEnedis.updateLastMethodCallError(self._myDataEnedis.getLastMethodCall())  # on met l'etat precedent
                    time.sleep( 10 )
                    # si pas ok, alors on fait un deuxième essai
                    _LOGGER.warning("%s - **** on va tenter un deuxème essai ***" %(self._myDataEnedis.get_PDL_ID()))
                    status_counts = sensorEnedis.manageSensorState(self._myDataEnedis, _LOGGER, __VERSION__)
                    if (self._myDataEnedis.getStatusLastCall() == False):
                        _LOGGER.warning("%s - **** ERROR *** %s" %(self._myDataEnedis.get_PDL_ID(), self._myDataEnedis.getLastMethodCall()))
                        self._myDataEnedis.updateLastMethodCallError(self._myDataEnedis.getLastMethodCall())  # on met l'etat precedent
                        self.setStateFromLastState()
                        status_counts = self.setAttributesFromLastAttributes()
                        status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
                        self._attributes.update(status_counts)
                        _LOGGER.warning("%s - **** fin ERROR *** %s" % ( self._myDataEnedis.get_PDL_ID(), self._myDataEnedis.getLastMethodCall()))
                        # si on a eut une erreur ... alors voir pour reprendre precedent ?
                else:
                    if ( not self._myDataEnedis.getUpdateRealise()): return # si pas d'update
                    self._attributes = {ATTR_ATTRIBUTION: ""}
                    self._attributes.update(status_counts)
                    if ( self._myDataEnedis.isProduction()):
                        self._state = status_counts['yesterday_production']*0.001
                    else:
                        self._state = status_counts['yesterday']*0.001
                    self.setLastState()
                    self.setLastAttributes()
            except:
                _LOGGER.warning("%s - **** CRASH *** " % (self._myDataEnedis.get_PDL_ID()))
                self._attributes = {ATTR_ATTRIBUTION: ""}
                self.setStateFromLastState()
                status_counts = self.setAttributesFromLastAttributes()
                status_counts['errorLastCall'] = self._myDataEnedis.getErrorLastCall()
                self._attributes.update(status_counts)

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return

        # ADDED CODE HERE
        #_LOGGER.warning("*** kyes : %s " %(state.attributes.keys()))
        # si seulement pas eut de mise à jour !!
        # si la clef yesterday est disponible dans l'element courant, alors c'est que l'on a eut une mise à jour
        if 'yesterday' not in self._attributes.keys() and 'yesterday_production' not in self._attributes.keys(): # pas plutot la key à checker ??
            self._state = state.state
            _LOGGER.warning("*** / / / \ \ \ *** mise a jour state precedent %s " % (self._state))
            self._attributes = state.attributes
            _LOGGER.warning("*** / / / \ \ \ *** mise a jour attributes precedent %s " %( self._attributes ))
            #on sauvegarde les elements pour les reprendre si errot
            self.setLastAttributes()
            self.setLastState()

