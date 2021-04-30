
try:
    from .const import (
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

except ImportError:
    from const import (
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )

import datetime, logging
log = logging.getLogger(__nameMyEnedis__)

from .myCheckData import myCheckData

class myContrat():
    def __init__(self, myCalli, token, PDL_ID, version):
        self._contract = None
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

    def getContractData(self, contract, clef, defaultValue):
        if clef in contract:
            return contract[ clef ]
        else:
            return defaultValue

    def checkDataContract(self, dataAnswer):
        if (dataAnswer.get("error_code",200) != 200 ):
            raise Exception('call', "error", dataAnswer["tag"])
        return True

    def updateContract(self, data=None):
        try:
            log.info("--updateContract --")
            if (data == None): data = self.CallgetDataContract()
            log.info("updateContract : data %s" % (data))
            if ( self.checkDataContract(data) ):
                log.info("updateContract(2) : data %s" % (data))
                self._contract = self.analyseValueContract(data)
            return data
        except Exception as inst:
            if (inst.args[:2] == ("call", "error")):
                log.warning("*" * 60)
                log.warning("%s - Erreur call" % (self.get_PDL_ID(),))
                self.updateTimeLastCall()
                self.updateStatusLastCall(False)
                message = "%s - %s" % (messages.getMessage(inst.args[2]), self.getLastAnswer())
                self.updateErrorLastCall(message)
                log.warning("%s - %s" % (self.get_PDL_ID(), self.getLastMethodCall()))
                raise Exception(inst)
            else:
                raise Exception(inst)

    def analyseValueContract(self, data):
        contract = None
        if data != None:  # si une valeur
            for x in data['customer']['usage_points']:
                if str(x["usage_point"]['usage_point_id']) == self._PDL_ID:
                    contract = {}
                    contract['contracts'] = x["contracts"]
                    contract['usage_point_status'] = x["usage_point"]["usage_point_status"]
                    contract['subscribed_power'] = self.getContractData(x["contracts"], "subscribed_power", "???")
                    contract["mode_PDL"] = [ _consommation, _production ]
                    #if "subscribed_power" in x["contracts"]:
                    #    contract["mode_PDL"].append(_consommation)
                    #    if( contract['usage_point_status'] == "no com" ):
                    #        contract["mode_PDL"].append(_production)
                    #else:
                    #    contract["mode_PDL"].append(_production)
                    contract['offpeak_hours'] = self.getContractData(x["contracts"], "offpeak_hours", [])
                    contract['last_activation_date'] = self.getContractData(x["contracts"], "last_activation_date", None)[:10]
        return contract

    def getContract(self):
        return self._contract
    def setContract(self, contract= None):
        self._contract = contract

    def getsubscribed_power(self):
        return self._contract['subscribed_power']

    def getoffpeak_hours(self):
        return self._contract['offpeak_hours']

    def getLastActivationDate(self):
        return self._contract['last_activation_date']

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