
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

import logging
log = logging.getLogger(__nameMyEnedis__)

class myContrat():
    def __init__(self, myCalli, token, PDL_ID, version, heuresCreusesON, heuresCreuses):
        self._contract = None
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

    def getContractData(self, contract, clef, defaultValue):
        if clef in contract:
            return contract[ clef ]
        else:
            return defaultValue

    def checkDataContract(self, dataAnswer):
        if ("error_code" in dataAnswer.keys()):
            if (dataAnswer["error_code"] == "UNKERROR_001"):
                return False
            raise Exception('call', "error", dataAnswer)
        elif (dataAnswer.get("error_code",200) != 200 ):
            raise Exception('call', "error", dataAnswer["tag"])
        elif (dataAnswer.get("error", "") == "token_refresh_401"):
            raise Exception('call', "error", dataAnswer["description"])
        return True

    def getUsagePointStatus(self):
        return self._contract['usage_point_status']

    def getHeuresCreuses(self):
        return self._heuresCreuses

    def getTypePDL(self):
        return self._contract["mode_PDL"]

    def updateContract(self, data=None):
        log.info("--updateContract : data %s" % (data))
        if (data == None): data = self.CallgetDataContract()
        log.info("updateContract : data %s" % (data))
        if ( self.checkDataContract(data) ):
            log.info("updateContract(2) : data %s" % (data))
            self._contract = self.analyseValueContract(data)
        return data


    def analyseValueContract(self, data):
        contract = None
        if data != None:  # si une valeur
            if ( 'customer' in data.keys()):
                for x in data['customer']['usage_points']:
                    if str(x["usage_point"]['usage_point_id']) == self._PDL_ID:
                        contract = {}
                        contract['contracts'] = x["contracts"]
                        contract['usage_point_status'] = x["usage_point"]["usage_point_status"]
                        contract['subscribed_power'] = self.getContractData(x["contracts"], "subscribed_power", "???")
                        contract["mode_PDL"] = [ _consommation, _production ]
                        contract['offpeak_hours'] = self.getContractData(x["contracts"], "offpeak_hours", [])
                        contract['last_activation_date'] = self.getContractData(x["contracts"], "last_activation_date", None)[:10]
        return contract

    def getValue(self):
        return self._contract

    def setContract(self, contract= None):
        self._contract = contract

    def getsubscribed_power(self):
        if self._contract == None:
            return None
        else:
            return self._contract['subscribed_power']

    def getoffpeak_hours(self):
        if self._contract == None:
            return None
        else:
            return self._contract['offpeak_hours']

    def getLastActivationDate(self):
        if self._contract == None:
            return None
        else:
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

    def getcleanoffpeak_hours(self, offpeak=None):
        if (offpeak == None): offpeak = self.getoffpeak_hours()
        if (offpeak != None) and (offpeak != []):
            offpeakClean1 = offpeak.split("(")[1].replace(")", "").replace("H", ":").replace(";", "-").split("-")
            opcnew = []
            deb = ""
            fin = ""
            lastopc = ""
            for opc in offpeakClean1:
                opc = opc.rjust(5).replace(" ", "0")
                if (lastopc != ""):
                    fin = opc
                    if (lastopc > opc):
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
        if ( self._heuresCreusesON ):
            opcnew = self.getcleanoffpeak_hours()
            if (heuresCreuses != None):
                self._heuresCreuses = heuresCreuses
            elif (self._heuresCreuses != None) and ( self._heuresCreuses != []):
                # on garde les heures creueses déja définie....
                # self._heuresCreuses = .....
                pass
            elif (opcnew != []):
                self._heuresCreuses = opcnew
            else:
                pass
        else:
            #pas d'heures creuses
            self._heuresCreuses = []


    def _getHCHPfromHour(self, heure):
        heurePleine = True
        if ( self._heuresCreuses is not None ):
            for heureCreuse in self._heuresCreuses:
                try:  # gestion du 00:00 en heure de fin de creneau
                    if (heure == {"24:00": "00:00"}[heureCreuse[1]]):
                        heurePleine = False
                except:
                    pass
                if (heureCreuse[0] < heure) and (heure <= heureCreuse[1]):
                    heurePleine = False
        return heurePleine
