from __future__ import annotations

try:
    from .const import (  # isort:skip
        __nameMyEnedis__,
        _ENEDIS_MyElectricData,
        _ENEDIS_EnedisGateway,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
    )

import datetime
import logging
import re
import sys

from . import apiconst as API

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
        self._serviceEnedis = None
        self._serverNameUrl = {'enedisGateway': "https://enedisgateway.tech/api",
                               'myElectricalData': "https://www.myelectricaldata.fr"}

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

    def setParam(self, PDL_ID: str, token: str, version: str, serviceEnedis: str):
        self._PDL_ID, self._token, self._version, self._serviceEnedis = \
            PDL_ID, token, version, serviceEnedis

    def getDefaultHeader(self) -> dict[str, str]:
        return {
            "Authorization": self._token,
            "Content-Type": self._contentType,
            "call-service": self._contentHeaderMyEnedis,
            "ha_sensor_myenedis_version": self._version,
        }

    def getServiceEnedis(self):
        return self._serviceEnedis

    def isMyElectricData(self, serviceEnedis):
        return serviceEnedis == _ENEDIS_MyElectricData

    def isEnedisGateway(self, serviceEnedis):
        return serviceEnedis == _ENEDIS_EnedisGateway

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
                f"={timestamp - myCall._lastTimeout}"
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

    def getUrl(self, serviceEnedis, data):
        if self.isMyElectricData(serviceEnedis):
            url = self._serverNameUrl[serviceEnedis]
            if data["type"] == "contracts":
                url = url + "/" + data["type"] + "/" + data["usage_point_id"] + "/"
            elif data["type"] == "daily_consumption":
                url = url + "/" + data["type"] + "/" + data["usage_point_id"] + "/" + \
                    "start" + "/" + data["start"] + "/" + \
                    "end" + "/" + data["end"] + "/"
            elif data["type"] == "daily_consumption_max_power":
                url = url + "/" + data["type"] + "/" + data["usage_point_id"] + "/" + \
                    "start" + "/" + data["start"] + "/" + \
                    "end" + "/" + data["end"] + "/"
            elif data["type"] == "daily_production":
                url = url + "/" + data["type"] + "/" + data["usage_point_id"] + "/" + \
                    "start" + "/" + data["start"] + "/" + \
                    "end" + "/" + data["end"] + "/"
            elif data["type"] == "consumption_load_curve":
                url = url + "/" + data["type"] + "/" + data["usage_point_id"] + "/" + \
                    "start" + "/" + data["start"] + "/" + \
                    "end" + "/" + data["end"] + "/"
            elif data["type"] == "rte/ecowatt":
                url = url + "/" + data["type"] + "/" + \
                    data["start"] + "/" + \
                    data["end"] + "/"
            elif data["type"] == "rte/tempo":
                url = url + "/" + data["type"] + "/" + \
                    data["start"] + "/" + \
                    data["end"] + "/"
            return "get", url
            # return "get", url + "cache"
        elif self.isEnedisGateway(serviceEnedis):
            url = self._serverNameUrl[serviceEnedis]
            return "post", url
        else:
            return None

    def post_and_get_json(self, serviceEnedis=None, params=None,
                          data=None, headers=None):
        import json
        import random
        import time

        import requests

        maxTriesToGo: int = 4  # Number of gateway requests that can be made
        dataAnswer = None
        minDelay: float = INITIAL_CALL_DELAY
        while maxTriesToGo > 0:
            maxTriesToGo -= 1
            hasError = True  # Suppose error, will be set to False if no exception
            try:
                if not myCall.isAvailable():
                    _LOGGER.warning(
                        "Nombre d'appels à l'API dépassé,"
                        " ou dernière erreur trop récente"
                    )
                    dataAnswer = {
                        API.ERROR_CODE: "UNAVAILABLE",
                        API.ENEDIS_RETURN: {
                            API.ENEDIS_RETURN_ERROR: "UNAVAILABLE",
                            API.ENEDIS_RETURN_MESSAGE: "Indisponible, essayez plus tard",
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
                method, url = self.getUrl(serviceEnedis, data)
                if method == "post":
                    response = session.post(
                        url,
                        params=params,
                        data=json.dumps(data),
                        headers=headers,
                        timeout=30,
                    )
                else:
                    response = session.get(
                        url,
                        params=params,
                        data=json.dumps(data),
                        headers=headers,
                        timeout=30,)
                # Write API result to file (test generation, debug)
                self.saveApiReturn(counter, response.text)

                response.raise_for_status()
                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)
                _LOGGER.info(f"{logPrefix}headers : {headers} =====")
                _LOGGER.info(f"{logPrefix}data : {data} =====")
                _LOGGER.info(f"{logPrefix}reponse : {dataAnswer} =====")
                maxTriesToGo = 0  # Done
                hasError = False
            except requests.exceptions.Timeout:
                myCall.handleTimeout()
                # a ajouter raison de l'erreur !!!
                _LOGGER.error(f"{logPrefix}requests.exceptions.Timeout")
                dataAnswer = {
                    API.ENEDIS_RETURN: {
                        API.ENEDIS_RETURN_ERROR: "UNKERROR_TIMEOUT",
                        API.ENEDIS_RETURN_MESSAGE: "Timeout",
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

                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)

                # Ne pas retenter l'appel,
                # Sauf si erreur côté enedis ("si le nombre de digit n'est pas de 14"),
                if (
                    "usage_point_id parameter must be 14 digits long."
                    not in response.text
                ):
                    maxTriesToGo = 0  # Fatal error, do not try again

            # Log result as error in case of exception, or as debug otherwise
            _LOGGER.log(
                logging.ERROR if hasError else logging.DEBUG,
                "Data answer: %r",
                dataAnswer,
            )

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
                self.getServiceEnedis(), data=payload, headers=headers
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
                self.getServiceEnedis(), data=payload, headers=headers
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
                self.getServiceEnedis(), data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataEcoWatt(self, deb, fin):
        if fin is not None:
            payload = {
                "type": "rte/ecowatt",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self.getServiceEnedis(), data=payload, headers=headers
            )
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataTempo(self, deb, fin):
        if fin is not None:
            payload = {
                "type": "rte/tempo",
                "usage_point_id": self._PDL_ID,
                "start": str(deb),
                "end": str(fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(
                self.getServiceEnedis(), data=payload, headers=headers
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
                self.getServiceEnedis(), data=payload, headers=headers
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
            self.getServiceEnedis(), data=payload, headers=headers
        )
        return dataAnswer
