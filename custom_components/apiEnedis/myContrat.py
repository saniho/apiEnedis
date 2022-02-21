from __future__ import annotations

from typing import Any

try:
    from .const import (  # isort:skip
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

import logging

log = logging.getLogger(__nameMyEnedis__)


class myContrat:
    _NULL_CONTRACT = {
        "contracts": None,
        "usage_point_status": None,
        "subscribed_power": "???",
        "mode_PDL": None,
        "offpeak_hours": (),
        "last_activation_date": None,
    }

    def __init__(self, myCalli, token, PDL_ID, version, heuresCreusesON, heuresCreuses):
        self._contract: dict[str, Any]
        self.setContract(None)
        self._heuresCreusesON = heuresCreusesON
        self._heuresCreuses = heuresCreuses
        self._token, self._PDL_ID, self._version = token, PDL_ID, version
        self.myCalli = myCalli

    def get_PDL_ID(self):
        return self._PDL_ID

    def get_token(self):
        return self._token

    def get_version(self):
        return self._version

    def CallgetDataContract(self):
        return self.myCalli.getDataContract()

    def getContractData(self, contract, clef):
        if clef in contract:
            return contract[clef]
        else:
            return myContrat._NULL_CONTRACT[clef]

    def checkDataContract(self, dataAnswer):
        if "error_code" in dataAnswer.keys():
            if dataAnswer["error_code"] == "UNKERROR_001":
                return False
            raise Exception("call", "error", dataAnswer)
        elif dataAnswer.get("error_code", 200) != 200:
            raise Exception("call", "error", dataAnswer["tag"])
        elif dataAnswer.get("error", "") == "token_refresh_401":
            raise Exception("call", "error", dataAnswer["description"])
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
            data = self.CallgetDataContract()
        log.debug(f"updateContract : data {data}")
        if self.checkDataContract(data):
            log.debug(f"updateContract(2) : data {data}")
            self.setContract(self.analyseValueContract(data))
        return data

    def analyseValueContract(self, data) -> dict[str, Any] | None:
        contract = None
        if data is not None and "customer" in data.keys():
            for x in data["customer"]["usage_points"]:
                usage_point = str(x["usage_point"]["usage_point_id"])
                if usage_point != self._PDL_ID:
                    continue

                contracts = x["contracts"]
                contract = {
                    "contracts": contracts,
                    "usage_point_status": usage_point,
                    "subscribed_power": self.getContractData(
                        contracts, "subscribed_power"
                    ),
                    "mode_PDL": [_consommation, _production],
                    "offpeak_hours": self.getContractData(contracts, "offpeak_hours"),
                    "last_activation_date": self.getContractData(
                        contracts, "last_activation_date"
                    )[:10],
                }
                break
        return contract

    def getValue(self):
        return self._contract

    def setContract(self, contract=None):
        if isinstance(contract, dict):
            self._contract = contract
        else:
            self._contract = myContrat._NULL_CONTRACT.copy()

    def getsubscribed_power(self):
        return self._contract["subscribed_power"]

    def getoffpeak_hours(self):
        return self._contract["offpeak_hours"]

    def getLastActivationDate(self):
        return self._contract["last_activation_date"]

    def minCompareDateContract(self, datePeriod):
        minDate = self.getLastActivationDate()
        if (minDate is not None) and (minDate > "%s" % datePeriod):
            return minDate
        else:
            return datePeriod

    def maxCompareDateContract(self, datePeriod):
        dateContract = self.getLastActivationDate()
        if (dateContract is not None) and (dateContract < "%s" % datePeriod):
            return datePeriod
        else:
            return None

    def getcleanoffpeak_hours(self, offpeak=None):
        if offpeak is None:
            offpeak = self.getoffpeak_hours()
        if (offpeak is not None) and (offpeak != []):
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
