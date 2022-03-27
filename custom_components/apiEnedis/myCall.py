from __future__ import annotations

try:
    from .const import (  # isort:skip
        __nameMyEnedis__,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
    )

import datetime
import logging
import re
import sys

_LOGGER = logging.getLogger(__nameMyEnedis__)

# Min and Max Delays for initial call and subsequent calls.
# The purpose is to make some random distribution between client calls
# so that clients do not sollicit the gateway at the sime time.
INITIAL_CALL_DELAY = 1.0  # Minimum time to wait for first call
NEXT_MIN_CALL_DELAY = 55.0  # Minimum Time to wait for second call and next calls
MAX_CALL_DELAY = 125.0  # Maximum Time to wait for call

if any(re.findall(r"pytest|py.test|testEnedis", sys.argv[0])):
    # Shorter delays during test
    INITIAL_CALL_DELAY = 0.250
    NEXT_MIN_CALL_DELAY = 0.5
    MAX_CALL_DELAY = 1.0

MAX_CALLS = 50
# In seconds - delay required since previous timeout to try a new call
MAX_PREVIOUS_TIMEOUT = 3600


class myCall:
    _MyCallsSinceRestart = 0
    _MyCallsUpdateDay = ""
    _lastTimeout = 0.0
    _noRecentTimeout = True

    def __init__(self):
        self._lastAnswer = None
        self._contentType = "application/json"
        self._contentHeaderMyEnedis = "home-assistant-myEnedis"
        self._serverName = "https://enedisgateway.tech/api"

    @staticmethod
    def sanitizeCounter() -> int:
        # Check if new day to reset the counter
        day = datetime.date.today().strftime("%Y-%m-%d")
        if day != myCall._MyCallsUpdateDay:
            # New day, reset counter
            myCall._MyCallsSinceRestart = 0
            myCall._MyCallsUpdateDay = day

        return myCall._MyCallsSinceRestart

    @staticmethod
    def increaseCallCounter() -> int:
        """Increase an get the number of service calls"""
        myCall.sanitizeCounter()

        myCall._MyCallsSinceRestart += 1
        return myCall._MyCallsSinceRestart

    def setParam(self, PDL_ID: str, token: str, version: str):
        self._PDL_ID, self._token, self._version = PDL_ID, token, version

    def getDefaultHeader(self) -> dict[str, str]:
        return {
            "Authorization": self._token,
            "Content-Type": self._contentType,
            "call-service": self._contentHeaderMyEnedis,
            "ha_sensor_myenedis_version": self._version,
        }

    def setLastAnswer(self, lastanswer):
        self._lastAnswer = lastanswer

    def getLastAnswer(self):
        return self._lastAnswer

    @staticmethod
    def isAvailable() -> bool:
        """Return true if the service is available"""
        # The serice is considered not available when:
        # - There were too many recent Timeouts
        # - The number of daily requests is exceeded
        if myCall.sanitizeCounter() >= MAX_CALLS:
            _LOGGER.debug("Nombre d'appels maximum journalier dépassé")
            return False

        if not myCall._noRecentTimeout:
            timestamp = datetime.datetime.now().timestamp()
            _LOGGER.debug(
                f"Ancien timeout? {timestamp}-{myCall._lastTimeout}"
                f"={timestamp-myCall._lastTimeout}"
                f"> {MAX_PREVIOUS_TIMEOUT} ?"
            )
            if timestamp - myCall._lastTimeout > MAX_PREVIOUS_TIMEOUT:
                myCall._noRecentTimeout = True

        return myCall._noRecentTimeout

    @staticmethod
    def handleTimeout():
        timestamp = datetime.datetime.now().timestamp()
        if timestamp - myCall._lastTimeout < MAX_PREVIOUS_TIMEOUT:
            myCall._noRecentTimeout = False

        myCall._lastTimeout = timestamp

    def saveApiReturn(self, idx: int, data: str):
        """Save return from API to index file to produce test data"""
        import os

        fname = os.path.dirname(__file__) + f"/myEnedis/test_data/data_{idx}.txt"
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        with open(fname, "w") as f:
            f.write(data)

    def post_and_get_json(self, url, params=None, data=None, headers=None):
        import json
        import random
        import time

        import requests

        maxTriesToGo: int = 4  # Number of gateway requests that can be made
        dataAnswer = None
        minDelay: float = INITIAL_CALL_DELAY
        while maxTriesToGo > 0:
            maxTriesToGo -= 1
            try:
                if not myCall.isAvailable():
                    dataAnswer = {
                        "error_code": "UNAVAILABLE",
                        "enedis_return": {
                            "error": "UNAVAILABLE",
                            "message": "Indisponible, essayez plus tard",
                        },
                    }
                    self.setLastAnswer(dataAnswer)
                    maxTriesToGo = 0
                    continue  # Next loop, so exit.

                # Wait some random time so that clients are not making requests
                # in the same second.
                sleepDuration = random.uniform(minDelay, MAX_CALL_DELAY)
                _LOGGER.debug(f"Sleeping {sleepDuration}s")
                time.sleep(sleepDuration)
                minDelay = NEXT_MIN_CALL_DELAY

                session = requests.Session()
                session.verify = True

                # Set up log prefix, with counter
                counter = myCall.increaseCallCounter()
                logPrefix = f"====== Appel http #{counter} !!! "
                _LOGGER.info(f"{logPrefix}=====")

                # raise(requests.exceptions.Timeout) # pour raiser un timeout de test ;)
                response = session.post(
                    url,
                    params=params,
                    data=json.dumps(data),
                    headers=headers,
                    timeout=30,
                )
                # Generate test data with next line
                self.saveApiReturn(counter, response.text)

                response.raise_for_status()
                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)
                _LOGGER.info(f"{logPrefix}headers : {headers} =====")
                _LOGGER.info(f"{logPrefix}data : {data} =====")
                _LOGGER.info(f"{logPrefix}reponse : {dataAnswer} =====")
                maxTriesToGo = 0  # Done
            except requests.exceptions.Timeout:
                myCall.handleTimeout()
                # a ajouter raison de l'erreur !!!
                _LOGGER.error(f"{logPrefix}requests.exceptions.Timeout")
                dataAnswer = {
                    "enedis_return": {
                        "error": "UNKERROR_TIMEOUT",
                        "message": "Timeout",
                    }
                }
                self.setLastAnswer(dataAnswer)
            except requests.exceptions.HTTPError:
                _LOGGER.error(f"{logPrefix}requests.exceptions.HTTPError")
                if ("ADAM-ERR0069" not in response.text) and (
                    "__token_refresh_401" not in response.text
                ):
                    _LOGGER.error("*" * 60)
                    _LOGGER.error(f"header : {headers} ")
                    _LOGGER.error(f"params : {params} ")
                    _LOGGER.error(f"data : {json.dumps(data)} ")
                    _LOGGER.error(f"Error JSON : {response.text} ")
                    _LOGGER.error("*" * 60)
                # with open('error.json', 'w') as outfile:
                #    json.dump(response.json(), outfile)
                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)

                # Ne pas retenter l'appel,
                # Sauf si erreur côté enedis ("si le nombre de digit n'est pas de 14"),
                if (
                    "usage_point_id parameter must be 14 digits long."
                    not in response.text
                ):
                    maxTriesToGo = 0  # Fatal error, do not try again

        _LOGGER.debug("Data answer: %r", dataAnswer)
        # if ( "enedis_return" in dataAnswer.keys() ):
        #    if ( type( dataAnswer["enedis_return"] ) is dict ):
        #        if ( "error" in dataAnswer["enedis_return"].keys()):
        #            if ( dataAnswer["enedis_return"]["error"] == "UNKERROR_TIMEOUT"):
        #                raise error
        return dataAnswer

    def getDataPeriod(self, deb: str, fin: str | None) -> tuple[str, bool]:
        if fin is not None:
            _LOGGER.info(f"--get dataPeriod : {deb} => {fin} --")
            payload = {
                "type": "daily_consumption",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self._serverName, data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataPeriodConsumptionMaxPower(self, deb, fin):
        if fin is not None:
            _LOGGER.info(f"--get dataPeriod : {deb} => {fin} --")
            payload = {
                "type": "daily_consumption_max_power",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self._serverName, data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataProductionPeriod(self, deb, fin):
        if fin is not None:
            payload = {
                "type": "daily_production",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self._serverName, data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataPeriodCLC(self, deb, fin):
        if fin is not None:
            payload = {
                "type": "consumption_load_curve",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self._serverName, data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataContract(self):
        payload = {
            "type": "contracts",
            "usage_point_id": self._PDL_ID,
        }
        headers = self.getDefaultHeader()
        dataAnswer = self.post_and_get_json(
            self._serverName, data=payload, headers=headers
        )
        return dataAnswer
