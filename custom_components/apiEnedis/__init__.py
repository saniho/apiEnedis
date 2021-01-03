"""my first component."""
from datetime import timedelta
import logging
try:
    from homeassistant.config_entries import SOURCE_IMPORT
    from homeassistant.const import (
        CONF_SCAN_INTERVAL,
        EVENT_HOMEASSISTANT_STARTED,
    )
    from homeassistant.core import CoreState, callback
    from homeassistant.exceptions import ConfigEntryNotReady

    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
except:
    # si py test
    class DataUpdateCoordinator:
        def __init__(self):
            pass
    def callback( var1 ):
        return
    pass

from . import sensorEnedis
from . import myEnedis

from .const import (
    CONF_TOKEN,
    CONF_CODE,
    DOMAIN,
    PLATFORM,
    HP_COST,
    HC_COST,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSOR_INTERVAL,
    myENEDIS_SERVICE,
    __VERSION__,
    CONF_DELAY,
)
_LOGGER = logging.getLogger(__name__)

"""async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    #Set up Meteo-France from legacy config file.
    conf = config.get(DOMAIN)
    if not conf:
        return True

    for city_conf in conf:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=city_conf
            )
        )

    return True
"""
async def async_setup(hass, config):
    """Import integration from config."""
    #conf = config.get(DOMAIN)
    #if not conf:
    #    return True
    #for enedisConf in conf:
    #    _LOGGER.exception("run myEnedis for %s"( enedisConf ))
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )
    return True


async def _async_setup_entry(hass, config_entry):
    "Set up this integration using UI."
    coordinator = sensorEnedisCoordinator( hass, config_entry)
    await coordinator.async_setup()

    async def _enable_scheduled_myEnedis(*_):
        """Activate the data update coordinator."""
        coordinator.update_interval = timedelta(
            #seconds=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            seconds=DEFAULT_SCAN_INTERVAL
        )
        await coordinator.async_refresh()

    if hass.state == CoreState.running:
        await _enable_scheduled_myEnedis()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady
    else:
        # Running a speed test during startup can prevent
        # integrations from being able to setup because it
        # can saturate the network interface.
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, _enable_scheduled_myEnedis
        )

    hass.data[DOMAIN] = coordinator
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, PLATFORM)
    )
    return True

async def async_setup_entry(hass, config_entry) -> bool:

    coordinator = sensorEnedisCoordinator( hass, config_entry)
    await coordinator.async_setup()
    async def _enable_scheduled_myEnedis(*_):
        """Activate the data update coordinator."""
        coordinator.update_interval = timedelta(
            seconds=config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        await coordinator.async_refresh()
    if hass.state == CoreState.running:
        await _enable_scheduled_myEnedis()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady
    else:
        # Running a speed test during startup can prevent
        # integrations from being able to setup because it
        # can saturate the network interface.
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, _enable_scheduled_myEnedis
        )
    undo_listener = config_entry.add_update_listener(update_listener)
    hass.data[DOMAIN] = coordinator
    for component in [PLATFORM]:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )
    return True

async def update_listener(hass, config_entry):
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass, config_entry):
    """Unload myEnedis Entry from config_entry."""
    hass.services.async_remove(DOMAIN, myENEDIS_SERVICE)

    hass.data[DOMAIN].async_unload()

    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")

    hass.data.pop(DOMAIN)

    return True

class sensorEnedisCoordinator( DataUpdateCoordinator):

    def __init__(self, hass, config_entry):
        """Initialize the data object."""
        self.hass = hass
        self.config_entry = config_entry
        self.myEnedis = None
        self.servers = {}
        self._unsub_update_listener = None
        super().__init__(
            self.hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self.async_update,
        )

    def update_data(self):
        """Get the latest data from myEnedis."""
        self.myEnedis.updateManagerSensor()
        return True

    async def async_update(self, *_):
        """Update myEnedis data."""
        try:
            return await self.hass.async_add_executor_job(self.update_data)
        except Exception as inst:
            raise Exception(inst)

    async def async_set_options(self):
        """Set options for entry."""
        _LOGGER.info("async_set_options - proc -- %s" %(self.config_entry.options))
        if not self.config_entry.options:
            _LOGGER.info(".config_entry.options()")
            data = {**self.config_entry.data}
            options = {
                CONF_SCAN_INTERVAL: data.pop(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                CONF_TOKEN: data.pop(CONF_TOKEN, ""),
                CONF_CODE: str(data.pop(CONF_CODE, "")),
                HP_COST: str(data.pop(HP_COST, "0.0")),
                HC_COST: str(data.pop(HC_COST, "0.0")),
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data, options=options
            )
            _LOGGER.info(".config_entry.options() - done")
        _LOGGER.info("async_set_options - proc -- done ")

    def update_MyEnedis(self):
        _LOGGER.info("update_MyEnedis")
        if (not self.myEnedis.getInit()):
            _LOGGER.info("getInit()")
            delai_interval = CONF_DELAY # delai de rafraichissement de l'appel API
            heuresCreusesCh = "[]"
            heuresCreuses = eval(heuresCreusesCh)
            HC_Cost_key = "hc_cout"
            HP_Cost_key = "hp_cout"
            if (HC_Cost_key not in self.config_entry.options.keys()):
                HCCost = float("0.0")
            else:
                HCCost = float(self.config_entry.options.get(HC_Cost_key, "0.0"))
            if (HP_Cost_key not in self.config_entry.options.keys()):
                HPCost = float("0.0")
            else:
                HPCost = float(self.config_entry.options.get(HP_Cost_key, "0.0"))
            token, code = self.config_entry.options['token'], self.config_entry.options['code']
            _LOGGER.info("options - proc -- %s %s %s %s" %(token, code, HPCost, HCCost))
            myDataEnedis = myEnedis.myEnedis(token, code, delai_interval, \
                                               heuresCreuses=heuresCreuses, heuresCreusesCost=HCCost,
                                               heuresPleinesCost=HPCost, log=_LOGGER)
            self.myEnedis.init(myDataEnedis, _LOGGER, __VERSION__)

    async def async_setup(self):
        """Set up myEnedis."""
        try:
            _LOGGER.info("run my First Extension")
            self.myEnedis = await self.hass.async_add_executor_job(sensorEnedis.manageSensorState)
            _LOGGER.info("run my First Extension - done -- ")
        except Exception as inst:
            raise Exception( inst )

        async def request_update(call):
            """Request update."""
            await self.async_request_refresh()
        await self.async_set_options()
        await self.hass.async_add_executor_job(self.update_MyEnedis)
        #_LOGGER.exception("async_add_executor_job -  ")
        #self.hass.services.async_register(DOMAIN, myENEDIS_SERVICE, request_update)
        #_LOGGER.exception("async_add_executor_job - done -- ")
        self._unsub_update_listener = self.config_entry.add_update_listener(
            options_updated_listener
        )
    @callback
    def async_unload(self):
        """Unload the coordinator."""
        if not self._unsub_update_listener:
            return
        self._unsub_update_listener()
        self._unsub_update_listener = None


async def options_updated_listener(hass, entry):
    """Handle options update."""

    _LOGGER.info("options_updated_listener ")
    hass.data[DOMAIN].update_interval = timedelta(
        seconds=DEFAULT_SENSOR_INTERVAL
    )
    await hass.data[DOMAIN].async_request_refresh()
    _LOGGER.info("options_updated_listener - done -- ")
