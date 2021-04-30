
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

class myYesterday():
    def __init__(self, myCalli, token, version, contrat):
        self.myCalli = myCalli
        self._yesterday = 0
        self._yesterdayDate = None
        self._contrat = contrat
        self._token, self._version = token, version

    def CallgetYesterday(self):
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = hier
        fin = cejour
        deb = self._contrat.minCompareDateContract(deb)
        fin = self._contrat.maxCompareDateContract(fin)
        val1, val2 = self.myCalli.getDataPeriod(hier, cejour)
        return val1, val2, hier

    def getYesterday(self):
        return self._yesterday

    def getYesterdayDate(self):
        return self._yesterdayDate

    def updateYesterday(self, data=None):
        log.info("--updateYesterday --")
        yesterdayDate = None
        if (data == None): data, callDone, yesterdayDate = self.CallgetYesterday()
        else: callDone = True
        log.info("updateYesterday : data %s" % (data))
        if (callDone ) and (myCheckData().checkData(data)):
            self._yesterday = myCheckData().analyseValue(data)
            self._yesterdayDate = yesterdayDate
        else:
            self._yesterday = 0
        return data