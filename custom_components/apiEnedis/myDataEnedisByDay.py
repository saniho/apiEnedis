
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

class myDataEnedisByDay():
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

    def updateData(self, clefFunction, data=None, dateDeb=None, dateFin=None, withControl = False):
        self._nbCall = 0
        onLance = True
        if withControl:
            if ( self._dateDeb == dateDeb and self._dateFin == dateFin and self._callOk ):
                onLance = False # pas de lancement si meme date
            else:
                self._callOk = None
        if onLance:
            self._dateDeb = dateDeb
            self._dateFin = dateFin
            log.info("--updateData %s ( du %s au %s )--" %( clefFunction, dateDeb, dateFin))
            #print("--updateData %s ( du %s au %s )--" %( clefFunction, dateDeb, dateFin))
            self._data = data
            if (self._data == None):
                if ( dateDeb == dateFin):
                    self._value = 0
                else:
                    self._data, callDone = self.CallgetData(dateDeb, dateFin)
                    if (callDone) and (myCheckData().checkDataPeriod(self._data)):
                        self._value = myCheckData().analyseValueAndAdd(self._data)
                        self._callOk = True
                        self._nbCall = 1
                    else:
                        self._value = 0
            else:
                callDone = True
                if (callDone) and (myCheckData().checkDataPeriod(self._data)):
                    self._value = myCheckData().analyseValueAndAdd(self._data)
                    self._callOk = True
                else:
                    self._value = 0
            log.info("with update !! %s ( du %s au %s )--" %( clefFunction, dateDeb, dateFin))
            log.info("updateData : data %s" % (self._data))
        else:
            log.info("noupdate !! %s ( du %s au %s )--" %( clefFunction, dateDeb, dateFin))
            log.info("no updateData : data %s" % (self._data))
        return self._data