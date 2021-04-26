""" Constants """

try:
    from homeassistant.const import (
        CONF_NAME,
        ATTR_ATTRIBUTION,
    )
except ImportError:
    # si py test
    class homeassistant:
        def __init__(self):
            # nothing to do
            pass

ISSUE_URL="https://github.com/saniho/apiEnedis/issues"
myENEDIS_SERVICE = "myEnedis"
# nom du repertoire
DOMAIN = "myEnedis"
DATA_UPDATED = f"{DOMAIN}_data_updated"

# Base component constants
PLATFORM = "sensor"

# Configuration
CONF_TOKEN = "token"
CONF_CODE = "code"
CONF_SCAN_INTERVAL = "conf_scan_interval" # 60 secondes verifications du coordinator

HP_COST = "hp_cout"
HC_COST = "hc_cout"

CONF_DELAY = 60 * 60 * 6  # verification enedis toutes les 6 heures
DEFAULT_SCAN_INTERVAL = 60*30  # verification enedis toutes les 30 minutes, si dernier ok, alors verifie selon conf_delay
#DEFAULT_SCAN_INTERVAL = 60*2  # verification enedis toutes les 30 minutes, si dernier ok, alors verifie selon conf_delay
DEFAULT_SENSOR_INTERVAL = 60 # 60 secondes verifications du coordinator
DEFAULT_SCAN_INTERVAL_HISTORIQUE = 60*10 # 1 fois toutes les 10 minutes

HEURESCREUSES_ON = "heuresCreusesON"
UNDO_UPDATE_LISTENER = "undo_update_listener"
COORDINATOR_ENEDIS = "coordinator_enedis"
__VERSION__ = "1.1.4.4rc2" # attention updater aussi manifest.json
__name__ = "myEnedis"

_consommation = "consommation"
_production = "production"

PLATFORMS = ["sensor"]

ENTITY_NAME = "name"
ENTITY_UNIT = "unit"
ENTITY_ICON = "icon"
ENTITY_DEVICE_CLASS = "device_class"
ENTITY_ENABLE = "enable"
ENTITY_API_DATA_PATH = "data_path"

SENSOR_TYPES = {
    "principal": {
        ENTITY_NAME: "principal",
        ENTITY_UNIT: "PRESSURE_HPA",
        ENTITY_ICON: None,
        ENTITY_DEVICE_CLASS: "DEVICE_CLASS_PRESSURE",
        ENTITY_ENABLE: False,
        ENTITY_API_DATA_PATH: "current_forecast:sea_level",
    }
}