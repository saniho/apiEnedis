""" Constants """


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
#CONF_DELAY = 60 * 2  # verification enedis toutes les 2 minutes
DEFAULT_SCAN_INTERVAL = 60*5  # verification enedis toutes les 5 minutes, si dernier ok, alors verif selon conf_delay
DEFAULT_SENSOR_INTERVAL = 60 # 60 secondes verifications du coordinator


__VERSION__ = "1.1.1.0"
__name__ = "myEnedis"