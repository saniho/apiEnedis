try:
    from .const import (
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

except ImportError:
    from const import (
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

import datetime, logging

log = logging.getLogger(__nameMyEnedis__)
from .myCheckData import myCheckData
from .myDataControl import okDataControl
from .myDataControl import getInformationDataControl


class myDataEnedisProduction:
    def __init__(self, myCalli, token, version, contrat):
        self.myCalli = myCalli
        self._value = 0
        self._date = None
        self._contrat = contrat
        self._token, self._version = token, version
        self._dateDeb = None
        self._dateFin = None
        self._callOk = None
        self._nbCall = 0
        self._data = None

    def CallgetData(self, dateDeb, dateFin):
        val1, val2 = self.myCalli.getDataProductionPeriod(dateDeb, dateFin)
        return val1, val2

    def getValue(self):
        return self._value

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
                    #... mais si on a quelque chose de ok avant, on le prendre
                    dateDeb, dateFin, self._callOk = getInformationDataControl( dataControl )
                    if self._callOk == None:
                        data = None  # si on doit mettre à jour .... sauf si on est pas la
                else:
                    self._callOk = None
                    data = None  # si on doit mettre à jour .... sauf si on est pas la
        if onLance:
            self._dateDeb = dateDeb
            self._dateFin = dateFin
            log.info(
                "--updateData %s ( du %s au %s )--" % (clefFunction, dateDeb, dateFin)
            )
            self._data = data
            if self._data is None:
                self._data, callDone = self.CallgetData(dateDeb, dateFin)
                self._nbCall = 1
            else:
                callDone = True
            log.info("updateData : data %s" % (self._data))
            if (callDone) and (myCheckData().checkData(self._data)):
                self._value = myCheckData().analyseValue(self._data)
                self._callOk = True
            else:
                self._value = 0
            self._callOk = callDone
            log.info(
                "with update !! %s ( du %s au %s )--" % (clefFunction, dateDeb, dateFin)
            )
            log.info("updateData : data %s" % (self._data))
        else:
            log.info(
                "noupdate !! %s ( du %s au %s )--" % (clefFunction, dateDeb, dateFin)
            )
            log.info("no updateData : data %s" % (self._data))
        return self._data
