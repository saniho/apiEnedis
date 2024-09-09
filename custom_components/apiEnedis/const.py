""" Constants """
from __future__ import annotations

import json
import logging
import os

LOGGER = logging.getLogger(__name__)
# version is fetched from manifest

__VERSION__: str
__name__ = "myEnedis"
VERSION_TIME: float
MANIFEST: dict[str, str | list[str]]


try:
    pass
except ImportError:
    # si py test
    class homeassistant:
        def __init__(self):
            # nothing to do
            pass


GITHUB_PRJ = "saniho/apiEnedis"
GITHUB_URL = f"https://github.com/{GITHUB_PRJ}"
ISSUE_URL = f"{GITHUB_URL}/issues"

# nom du repertoire
DOMAIN = "myEnedis"
DATA_UPDATED = f"{DOMAIN}_data_updated"

# Base component constants
PLATFORM = "sensor"

# Configuration
CONF_TOKEN = "token"
CONF_CODE = "code"
# defaut
CONF_SERVICE_ENEDIS = "enedisGateway"

# 60 secondes verifications du coordinator
CONF_SCAN_INTERVAL = "conf_scan_interval"

HP_COST = "hp_cout"
HC_COST = "hc_cout"
HEURES_CREUSES = "heures_creuses"

DEFAULT_REPRISE_ERR = 60 * 60  # verification enedis toutes les heures
DEFAULT_SCAN_INTERVAL = 2 * 60  # verification enedis toutes les 60 secondes
DEFAULT_SCAN_INTERVAL_HISTORIQUE = 60 * 10  # 1 fois toutes les 10 minutes

HEURESCREUSES_ON = "heuresCreusesON"
UNDO_UPDATE_LISTENER = "undo_update_listener"
UPDATE_LISTENER = "update_listener"
EVENT_UPDATE_ENEDIS = "update_enedis"
COORDINATOR_ENEDIS = "coordinator_enedis"

__nameMyEnedis__ = "myEnedis"
_consommation = "consommation"
_production = "production"

_ENEDIS_MyElectricData = "myElectricalData"
_ENEDIS_EnedisGateway = "enedisGateway"

PLATFORMS = ["sensor"]

_formatDateYmd = "%Y-%m-%d"
_formatDateYmdHMS = "%Y-%m-%d %H:%M:%S"

ENTITY_NAME = "name"
ENTITY_DELAI = "delai"

SENSOR_TYPES: dict[str, dict[str, int | str]] = {
    "principal": {
        ENTITY_NAME: "principal",
        ENTITY_DELAI: 60,
    },
    "principal_production": {
        ENTITY_NAME: "principal_production",
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
    "energy": {
        ENTITY_NAME: "energy",
        ENTITY_DELAI: 60,
    },
    "energyDetailHours": {
        ENTITY_NAME: "energyDetailHours",
        ENTITY_DELAI: 60,
    },
    "energyDetailHoursCost": {
        ENTITY_NAME: "energyDetailHoursCost",
        ENTITY_DELAI: 60,
    },
    "ecowatt": {
        ENTITY_NAME: "ecowatt",
        ENTITY_DELAI: 60,
    },
    "tempo": {
        ENTITY_NAME: "tempo",
        ENTITY_DELAI: 60,
    },
}


def getVersion() -> str:
    # Set name with regards to local path
    global VERSION_TIME
    global __VERSION__
    global MANIFEST

    fname = os.path.dirname(__file__) + "/manifest.json"

    ftime: float = 0
    try:
        VERSION_TIME
    except NameError:
        VERSION_TIME = 0
        __VERSION__ = "Unknown"
        MANIFEST = {}

    try:
        ftime = os.path.getmtime(fname)
        if ftime != ftime:
            __VERSION__ = "Unknown"
            MANIFEST = {}
    except Exception:
        MANIFEST = {}

    if (__VERSION__ is None and ftime != 0) or (ftime != VERSION_TIME):
        # No version, or file change -> get version again
        LOGGER.debug(f"Read version from {fname} {ftime}<>{VERSION_TIME}")

        with open(fname) as f:
            VERSION_TIME = ftime
            MANIFEST = json.load(f)

        if MANIFEST is not None:
            if "version" in MANIFEST.keys():
                v = MANIFEST["version"]
                __VERSION__ = v if isinstance(v, str) else "Invalid manifest"
                if __VERSION__ == "0.0.0":
                    __VERSION__ = "dev"

    return __VERSION__


getVersion()
