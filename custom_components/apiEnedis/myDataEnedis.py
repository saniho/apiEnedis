
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

class myDataEnedis():
    def __init__(self, myCalli, token, version, contrat):
        self.myCalli = myCalli
        self._value = 0
        self._date = None
        self._contrat = contrat
        self._token, self._version = token, version
        self._nbCall = 0

    def CallgetData(self, dateDeb, dateFin):
        val1, val2 = self.myCalli.getDataPeriod(dateDeb, dateFin)
        return val1, val2

    def getValue(self):
        return self._value

    def getDateFin(self):
        return self._dateFin

    def getDateDeb(self):
        return self._dateDeb

    def getNbCall(self):
        return self._nbCall

    def updateData(self, clefFunction, data=None, dateDeb=None, dateFin=None):
        self._nbCall = 0
        self._dateDeb = dateDeb
        self._dateFin = dateFin
        log.info("--updateData %s ( du %s au %s ) data:%s--" %( clefFunction, dateDeb, dateFin, data))
        if (data == None):
            if (dateDeb == dateFin):
                self._value = 0
            else:
                data, callDone = self.CallgetData(dateDeb, dateFin)
                self._nbCall = 1
                if (callDone ) and (myCheckData().checkData(data)):
                    self._value = myCheckData().analyseValue(data)
                else:
                    self._value = 0
        else:
            callDone = True
            if (callDone) and (myCheckData().checkData(data)):
                self._value = myCheckData().analyseValue(data)
                self._nbCall = 1
            else:
                self._value = 0
        log.info("updateData : data %s" % (data))
        return data