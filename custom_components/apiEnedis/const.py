""" Constants """
# attention updater aussi manifest.json
__VERSION__ = "1.3.1.14"
__name__ = "myEnedis"

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

ISSUE_URL = "https://github.com/saniho/apiEnedis/issues"
myENEDIS_SERVICE = "myEnedis"
# nom du repertoire
DOMAIN = "myEnedis"
DATA_UPDATED = f"{DOMAIN}_data_updated"

# Base component constants
PLATFORM = "sensor"

# Configuration
CONF_TOKEN = "token"
CONF_CODE = "code"

# 60 secondes verifications du coordinator
CONF_SCAN_INTERVAL = "conf_scan_interval"

HP_COST = "hp_cout"
HC_COST = "hc_cout"
HEURES_CREUSES = "heures_creuses"

CONF_DELAY = 60 * 60 * 6  # verification enedis toutes les 6 heures
DEFAULT_REPRISE_ERR = 60 * 60  # verification enedis toutes les heures
DEFAULT_SCAN_INTERVAL = 2 * 60  # verification enedis toutes les 60 secondes
DEFAULT_SENSOR_INTERVAL = 60 # 60 secondes verifications du coordinator
DEFAULT_SCAN_INTERVAL_HISTORIQUE = 60 * 10 # 1 fois toutes les 10 minutes

HEURESCREUSES_ON = "heuresCreusesON"
UNDO_UPDATE_LISTENER = "undo_update_listener"
COORDINATOR_ENEDIS = "coordinator_enedis"

__nameMyEnedis__ = "myEnedis"
_consommation = "consommation"
_production = "production"

PLATFORMS = ["sensor"]

_formatDateYmd = "%Y-%m-%d"
_formatDateYm01 = "%Y-%m-01"
_formatDateY0101 = "%Y-01-01"

ENTITY_NAME = "name"
ENTITY_DELAI = "delai"

SENSOR_TYPES = {
    "principal": {
        ENTITY_NAME: "principal",
        ENTITY_DELAI: 60,
    },
    "history_all": {
        ENTITY_NAME: "history_all",
        ENTITY_DELAI: 60,
    },
    "history_hp": {
        ENTITY_NAME: "history_hp",
        ENTITY_DELAI: 60,
    },
    "history_hc": {
        ENTITY_NAME: "history_hc",
        ENTITY_DELAI: 60,
    },
    "yesterdayCost": {
        ENTITY_NAME: "yesterdayCost",
        ENTITY_DELAI: 60,
    },
}
