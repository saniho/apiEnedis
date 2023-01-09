from __future__ import annotations

try:
    from .const import (  # isort:skip
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYmdHMS,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYmdHMS,
    )

import datetime
import logging

from .myCheckData import myCheckData
from .myDataControl import getInformationDataControl, okDataControl

log = logging.getLogger(__nameMyEnedis__)


class myDataEnedisByDayDetail:
    def __init__(self, myCalli, token, version, contrat, multiDays=False):
        self.myCalli = myCalli
        self._value = 0
        self._date = None
        self._contrat = contrat
        self._token, self._version = token, version
        self._interval_length = 1
        self._HP: dict | float = 0  # dict si multiDays
        self._HC: dict | float = 0  # dict si multiDays
        self._multiDays: bool = multiDays
        self._dateDeb = None
        self._dateFin = None
        self._callOk: bool | None = None
        self._nbCall = 0
        self._data = None

        self._joursHC = {}
        self._joursHP = {}
        self._dateHeureDetail = {}
        self._dateHeureDetailHC = {}
        self._dateHeureDetailHP = {}

    def getHP(self):
        return self._HP

    def getHC(self):
        return self._HC

    def getDaysHP(self):
        return self._joursHP

    def getDaysHC(self):
        return self._joursHC

    def getDateHeureDetail(self):
        return self._dateHeureDetail

    def getDateHeureDetailHC(self):
        return self._dateHeureDetailHC

    def getDateHeureDetailHP(self):
        return self._dateHeureDetailHP

    def CallgetData(self, dateDeb, dateFin):
        val1, val2 = self.myCalli.getDataPeriodCLC(dateDeb, dateFin)
        return val1, val2

    def getDateFin(self):
        return self._dateFin

    def getDateDeb(self):
        return self._dateDeb

    def getCallOk(self):
        return self._callOk

    def getNbCall(self):
        return self._nbCall

    def updateData(
        self,
        clefFunction,
        horairePossible=True,
        data=None,
        dateDeb=None,
        dateFin=None,
        withControl=False,
        dataControl=None,
    ):
        self._nbCall = 0
        onLance = True
        if withControl:
            if okDataControl(clefFunction, dataControl, dateDeb, dateFin):
                onLance = True
                self._callOk = True
            else:
                if not horairePossible:
                    onLance = True
                    dateDeb, dateFin, self._callOk = getInformationDataControl(
                        dataControl
                    )
                    if self._callOk is None:
                        data = (
                            None  # si on doit mettre à jour .... sauf si on est pas la
                        )
                else:
                    self._callOk = None
                    data = None  # si on doit mettre à jour .... sauf si on est pas la
        if onLance:
            self._dateDeb = dateDeb
            self._dateFin = dateFin
            log.info(
                f"--updateData {clefFunction} (du {self._dateDeb} au {self._dateFin})--"
            )
            self._data = data
            if self._data is None:
                self._data, callDone = self.CallgetData(self._dateDeb, self._dateFin)
                self._nbCall = 1
            else:
                callDone = True
            log.info("updateData : data %s", self._data)
            if self._multiDays:
                if self._dateDeb == self._dateFin:
                    self._HC, self._HP = {}, {}
                else:
                    if (callDone) and (myCheckData().checkDataPeriod(self._data)):
                        (
                            self._joursHC,
                            self._joursHP,
                        ) = self.createMultiDaysHCHP(self._data)
                        self._callOk = True
                    else:
                        self._HC, self._HP = {}, {}
                    self._callOk = callDone
            else:
                if self._dateDeb == self._dateFin:
                    self._HC, self._HP = 0, 0
                else:
                    if (callDone) and (myCheckData().checkData(self._data)):
                        self.createHCHP(self._data)
                        self._callOk = True
                    else:
                        self._HC, self._HP = 0, 0
                    self._callOk = callDone
            log.info(
                f"with update !! {clefFunction} (du {self._dateDeb} au {self._dateFin})"
            )
            log.info(f"updateData : data {self._data}")
        else:
            log.info(f"noupdate !! {clefFunction} (du {dateDeb} au {dateFin})")
            log.info(f"no updateData : data {self._data}")
        return self._data

    def getCoeffIntervalLength(self):
        interval = self.getIntervalLength()
        coeff: float = 1
        if interval == "PT10M":
            coeff = 1 * 10 / 60
        if interval == "PT15M":
            coeff = 1 * 15 / 60
        if interval == "PT20M":
            coeff = 1 * 20 / 60
        if interval == "PT30M":
            coeff = 1 * 30 / 60
        if interval == "PT60M":
            coeff = 1
        return coeff

    def getIntervalLength(self):
        return self._interval_length

    def createMultiDaysHCHP(self, data):
        joursHC = {}
        joursHP = {}
        # dateDuJour = (datetime.date.today()).strftime(_formatDateYmd)
        for x in data["meter_reading"]["interval_reading"]:
            self._interval_length = x["interval_length"]
            # date est la date de fin de la plage
            # on recule d'une minute .. car la date et l'heure est la fin de la plage
            newDate = (datetime.datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S")
                       - datetime.timedelta(minutes=1))\
                .strftime(_formatDateYmdHMS)
            date = newDate[:10]
            heure = newDate[11:16]
            if (
                heure == "00:00"
            ):  # alors sur la veille, car c'est la fin de la tranche du jour precedent
                date = (
                    datetime.datetime.strptime(date, "%Y-%m-%d") - datetime.timedelta(1)
                ).strftime(_formatDateYmd)

            # if ( date == dateDuJour ):
            #    print("ici", x["date"], x["value"])
            #    pass
            # else:
            if 1:
                if date not in joursHC:
                    joursHC[date] = 0
                if date not in joursHP:
                    joursHP[date] = 0
                heurePleine = self._contrat._getHCHPfromHour(heure)
                # clef contient la date et l'heure .. pas les minutes
                clef = x["date"][:13]
                if clef not in self._dateHeureDetail.keys():
                    self._dateHeureDetail[clef] = 0
                self._dateHeureDetail[clef] += (
                    int(x["value"]) * self.getCoeffIntervalLength()
                )
                if heurePleine:
                    joursHP[date] += (
                        int(x["value"]) * self.getCoeffIntervalLength()
                    )  # car c'est en heure
                    if clef not in self._dateHeureDetailHP.keys():
                        self._dateHeureDetailHP[clef] = 0
                    self._dateHeureDetailHP[clef] += (
                        int(x["value"]) * self.getCoeffIntervalLength()
                    )
                else:
                    joursHC[date] += (
                        int(x["value"]) * self.getCoeffIntervalLength()
                    )  # car c'est pas en heure
                    if clef not in self._dateHeureDetailHC.keys():
                        self._dateHeureDetailHC[clef] = 0
                    self._dateHeureDetailHC[clef] += (
                        int(x["value"]) * self.getCoeffIntervalLength()
                    )

        return joursHC, joursHP

    def createHCHP(self, data):
        self._HP = 0
        self._HC = 0
        for x in data["meter_reading"]["interval_reading"]:
            self._interval_length = x["interval_length"]
            heure = x["date"][11:16]
            heurePleine = self._contrat._getHCHPfromHour(heure)
            if heurePleine:
                self._HP += (
                    int(x["value"]) * self.getCoeffIntervalLength()
                )  # car par tranche de 30 minutes
            else:
                self._HC += (
                    int(x["value"]) * self.getCoeffIntervalLength()
                )  # car par tranche de 30 minutes
