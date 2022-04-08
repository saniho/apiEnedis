from __future__ import annotations

import logging
from typing import Any

from . import apiconst as API

try:
    from .const import (  # isort:skip
        _consommation,
        _production,
        __nameMyEnedis__,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
        _consommation,
        _production,
    )


log = logging.getLogger(__nameMyEnedis__)


class myContrat:
    _NULL_CONTRACT = {
        "is_loaded": False,
        "contracts": None,
        "usage_point_status": None,
        "subscribed_power": "???",
        "mode_PDL": None,
        "offpeak_hours": (),
        "last_activation_date": None,
    }

    def __init__(
        self,
        myCalli,
        token: str,
        PDL_ID: str,
        version: str,
        heuresCreusesON: bool,
        heuresCreuses: list | tuple | None,
    ):
        self._contract: dict[str, Any]
        self.__setContract(None)
        self._heuresCreusesON = heuresCreusesON
        self._heuresCreuses: list | tuple | None = heuresCreuses
        self._token, self._PDL_ID, self._version = token, PDL_ID, version
        self.myCalli = myCalli

    def get_PDL_ID(self):
        return self._PDL_ID

    def get_token(self):
        return self._token

    def get_version(self):
        return self._version

    def __callGetDataContract(self):
        return self.myCalli.getDataContract()

    def __contractField(self, contract, clef):
        if clef in contract:
            return contract[clef]
        else:
            return myContrat._NULL_CONTRACT[clef]

    def __checkDataContract(self, dataAnswer):
        if API.ERROR_CODE in dataAnswer.keys():
            if dataAnswer[API.ERROR_CODE] == "UNKERROR_001":
                return False
            raise Exception("call", "error", dataAnswer)
        elif dataAnswer.get(API.ERROR_CODE, 200) != 200:
            raise Exception("call", "error", dataAnswer[API.TAG])
        elif dataAnswer.get("error", "") == "token_refresh_401":
            raise Exception("call", "error", dataAnswer[API.DESCRIPTION])
        return True

    def getUsagePointStatus(self):
        return self._contract["usage_point_status"]

    def getHeuresCreuses(self):
        return self._heuresCreuses

    def getTypePDL(self):
        return self._contract["mode_PDL"]

    def updateContract(self, data=None):
        log.debug(f"--updateContract : data {data}")
        if data is None:
            data = self.__callGetDataContract()
        log.debug(f"updateContract : data {data}")
        if self.__checkDataContract(data):
            log.debug(f"updateContract(2) : data {data}")
            self.__setContract(self.__analyseValueContract(data))
        return data

    def __analyseValueContract(self, data) -> dict[str, Any] | None:
        contract = None
        if data is not None and "customer" in data.keys():
            for x in data["customer"]["usage_points"]:
                usage_point = str(x["usage_point"]["usage_point_id"])
                if usage_point != self._PDL_ID:
                    continue

                contracts = x["contracts"]
                contract = {
                    "is_loaded": True,
                    "contracts": contracts,
                    "usage_point_status": usage_point,
                    "subscribed_power": self.__contractField(
                        contracts, "subscribed_power"
                    ),
                    "mode_PDL": [_consommation, _production],
                    "offpeak_hours": self.__contractField(contracts, "offpeak_hours"),
                    "last_activation_date": self.__contractField(
                        contracts, "last_activation_date"
                    )[:10],
                }
                break
        return contract

    def __setContract(self, contract=None):
        if isinstance(contract, dict):
            self._contract = contract
        else:
            self._contract = myContrat._NULL_CONTRACT.copy()

    @property
    def isLoaded(self):
        return self._contract["is_loaded"]

    def getsubscribed_power(self):
        return self._contract["subscribed_power"]

    def getoffpeak_hours(self) -> str | None:
        return self._contract["offpeak_hours"]

    def getLastActivationDate(self):
        return self._contract["last_activation_date"]

    def minCompareDateContract(self, datePeriod):
        minDate = self.getLastActivationDate()
        if (minDate is not None) and (minDate > str(datePeriod)):
            return minDate
        else:
            return datePeriod

    def maxCompareDateContract(self, datePeriod):
        dateContract = self.getLastActivationDate()
        if (dateContract is not None) and (dateContract < str(datePeriod)):
            return datePeriod
        else:
            return None

    def getcleanoffpeak_hours(self, offpeak=None):
        if not isinstance(offpeak, (list, tuple)):
            offpeak = self.getoffpeak_hours()
        if isinstance(offpeak, str) and (len(offpeak) > 0):
            offpeakClean1 = (
                offpeak.split("(")[1]
                .replace(")", "")
                .replace("H", ":")
                .replace(";", "-")
                .split("-")
            )
            opcnew = []
            deb = ""
            fin = ""
            lastopc = ""
            for opc in offpeakClean1:
                opc = opc.rjust(5).replace(" ", "0")
                if lastopc != "":
                    fin = opc
                    if lastopc > opc:
                        fin = "23:59"
                        opcnew.append([deb, fin])
                        deb = "00:00"
                        fin = opc
                    opcnew.append([deb, fin])
                    deb = opc
                else:
                    deb = opc
                lastopc = opc
        else:
            opcnew = []
        return opcnew

    def updateHCHP(self, heuresCreuses=None):
        if self._heuresCreusesON:
            opcnew = self.getcleanoffpeak_hours()
            if heuresCreuses is not None:
                self._heuresCreuses = heuresCreuses
            elif (self._heuresCreuses is not None) and (self._heuresCreuses != []):
                # on garde les heures creueses déja définie....
                # self._heuresCreuses = .....
                pass
            elif opcnew != []:
                self._heuresCreuses = opcnew
            else:
                pass
        else:
            # pas d'heures creuses
            self._heuresCreuses = []

        if self._heuresCreuses is None:
            self._heuresCreuses = []

    # TODO: Not a private method, remove '_'
    def _getHCHPfromHour(self, heure):
        heurePleine = True
        if self._heuresCreuses is not None:
            for heureCreuse in self._heuresCreuses:
                try:  # gestion du 00:00 en heure de fin de creneau
                    if heure == {"24:00": "00:00"}[heureCreuse[1]]:
                        heurePleine = False
                except:
                    pass
                if (heureCreuse[0] <= heure) and (heure < heureCreuse[1]):
                    heurePleine = False
        return heurePleine
