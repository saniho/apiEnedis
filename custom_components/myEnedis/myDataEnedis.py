from __future__ import annotations

try:
    from .const import (  # isort:skip
        __nameMyEnedis__,
    )

except ImportError:
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
    )

import logging

from .myCall import myCall
from .myCheckData import myCheckData
from .myContrat import myContrat
from .myDataControl import okDataControl

log = logging.getLogger(__nameMyEnedis__)


class myDataEnedis:
    def __init__(self, myCalli: myCall, token: str, version: str, contrat: myContrat):
        self.myCalli = myCalli
        self._value = 0
        self._date = None
        self._contrat = contrat
        self._token, self._version = token, version
        self._dateDeb: str | None = None
        self._dateFin: str | None = None
        self._callOk: bool | None = None
        self._nbCall: int = 0
        self._data: str | None = None

    def CallgetData(self, dateDeb, dateFin) -> tuple[str, bool]:
        val1, val2 = self.myCalli.getDataPeriod(dateDeb, dateFin)
        return val1, val2

    def getValue(self) -> int:
        return self._value

    def getDateFin(self) -> str | None:
        return self._dateFin

    def getDateDeb(self) -> str | None:
        return self._dateDeb

    def getCallOk(self) -> bool | None:
        return self._callOk

    def getNbCall(self) -> int:
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
    ) -> str | None:
        self._nbCall = 0
        onLance = True
        if withControl:
            if okDataControl(clefFunction, dataControl, dateDeb, dateFin):
                onLance = True
                self._callOk = True
            else:
                if not horairePossible:
                    onLance = False
                    # si horaire non ok, on garde quand meme ce qui était
                    #   passé en parametre..cas du reboot
                    self._data = data
                else:
                    self._callOk = None
                    # si on doit mettre à jour .... sauf si on est pas la
                    data = None
        if onLance:
            self._dateDeb = dateDeb
            self._dateFin = dateFin
            log.info(
                "--updateData %s ( du %s au %s ) data:%s--",
                clefFunction,
                dateDeb,
                dateFin,
                data,
            )
            self._data = data
            if self._data is None:
                if dateDeb == dateFin:
                    self._value = 0
                else:
                    self._data, callDone = self.CallgetData(dateDeb, dateFin)
                    self._nbCall = 1
                    if (callDone) and (myCheckData().checkData(self._data)):
                        self._value = myCheckData().analyseValue(self._data)
                        self._callOk = True
                    else:
                        self._value = 0
                    self._callOk = callDone
            else:
                callDone = True
                if (callDone) and (myCheckData().checkData(self._data)):
                    self._value = myCheckData().analyseValue(self._data)
                    self._callOk = True
                    self._nbCall = 1
                else:
                    self._value = 0
                self._callOk = callDone
            log.info(f"with update !! {clefFunction} ( du {dateDeb} au {dateFin} )--")
            log.info(f"updateData : data {self._data}")
        else:
            log.info(f"noupdate !! {clefFunction} ( du {dateDeb} au {dateFin} )--")
            log.info(f"no updateData : data {self._data}")
        return self._data
