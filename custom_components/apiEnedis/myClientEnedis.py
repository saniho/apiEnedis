import datetime, sys
import logging, traceback

try:
    from .const import (
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )
    from . import messages
    from . import gitinformation

except ImportError:
    import messages
    from const import (
        _consommation,
        _production,
        __nameMyEnedis__,
        _formatDateYmd,
        _formatDateYm01,
        _formatDateY0101,
    )
    import gitinformation


from .myCall import myCall
myCalli = myCall()

from .myContrat import myContrat
from .myDataEnedis import myDataEnedis
from .myDataEnedisProduction import myDataEnedisProduction
from .myDataEnedisByDay import myDataEnedisByDay
from .myDataEnedisByDayDetail import myDataEnedisByDayDetail
from .myDataEnedisMaxPower import myDataEnedisMaxPower

log = logging.getLogger(__nameMyEnedis__)

class myClientEnedis:
    def __init__(self, token, PDL_ID, delai=3600, heuresCreuses=None, \
                 heuresCreusesCost=0, heuresPleinesCost=0, version="0.0.0",
                 heuresCreusesON=True):
        self._token = token
        self._PDL_ID = PDL_ID
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall = True
        self._errorLastCall = None
        self._errorLastMethodCall = None
        self._errorLastMethodCallError = None
        self._delai = delai
        self._heuresCreusesCost = heuresCreusesCost
        self._heuresPleinesCost = heuresPleinesCost
        self._updateRealise = False
        self._nbCall = 0
        self._niemeAppel = 0
        self._version = version
        self._forceCallJson = False

        myCalli.setParam( PDL_ID, token, version)
        self._contract = myContrat( myCalli, self._token, self._PDL_ID, self._version, heuresCreusesON, heuresCreuses)
        self._yesterday = myDataEnedis( myCalli, self._token, self._version, self._contract)
        self._yesterdayLastYear = myDataEnedis( myCalli, self._token, self._version, self._contract)
        self._currentWeek = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._currentWeekLastYear = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._lastWeek = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._last7Days = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._currentMonth = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._currentMonthLastYear = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._lastMonth = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._lastMonthLastYear = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._currentYear = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._lastYear = myDataEnedisByDay( myCalli, self._token, self._version, self._contract)
        self._yesterdayHCHP = myDataEnedisByDayDetail( myCalli, self._token, self._version, self._contract)
        self._last7DaysDetails = myDataEnedisByDayDetail( myCalli, self._token, self._version, self._contract, True)

        self._productionYesterday = myDataEnedisProduction( myCalli, self._token, self._version, self._contract)

        self._yesterdayConsumptionMaxPower = myDataEnedisMaxPower( myCalli, self._token, self._version, self._contract)
        log.info("run myEnedis")
        self._gitVersion = None
        self._dataJsonDefault = {}
        self._dataJson = {}
        pass

    def setUpdateRealise(self, value):
        self._updateRealise = value

    def getUpdateRealise(self):
        return self._updateRealise

    def setPathArchive(self, path):
        self._path = path

    def readDataJson(self):
        import glob, os, json
        data = {}
        dataRepertoire = self.getPathArchive()
        log.info("fichier lu dataRepertoire : %s" %dataRepertoire )
        directory = "%s/*.json" %dataRepertoire
        log.info("fichier lu directory : %s" %directory )
        listeFile = glob.glob(directory)
        log.info("fichier lu listeFile : %s" %listeFile )
        for nomFichier in listeFile:
            with open(nomFichier) as json_file:
                clef = os.path.basename(nomFichier).split(".")[0]
                data[clef] = json.load(json_file)
        return data

    def manageLastCallJson(self):
        lastCallInformation = self.getDataJson("lastCall")
        log.info("manageLastCallJson : ")
        if ( lastCallInformation != None):
            lastCall = lastCallInformation.get("timeLastCall", None)
            log.info("manageLastCallJson : lastCall : %s" %lastCall)
            if ( lastCall != None ):
                lastCall = datetime.datetime.strptime(lastCall, '%Y-%m-%d %H:%M:%S.%f')
                self.updateTimeLastCall( lastCall )
            lastUpdate = lastCallInformation.get("lastUpdate", None)
            log.info("manageLastCallJson : lastUpdate : %s" %lastUpdate)
            if ( lastUpdate != None ):
                lastUpdate = datetime.datetime.strptime(lastUpdate, '%Y-%m-%d %H:%M:%S.%f')
                self.updateLastUpdate(lastCall)
            statutLastCall = lastCallInformation.get("statutLastCall", None)
            log.info("manageLastCallJson : statutLastCall : %s" %statutLastCall)
            if ( statutLastCall != None ):
                self.updateStatusLastCall(statutLastCall)
            #timeLastUpdate = lastCallInformation.get("timeLastUpdate", None)
            #if ( timeLastUpdate != None ):
            #    timeLastUpdate = datetime.datetime.strptime(timeLastUpdate, '%Y-%m-%d %H:%M:%S.%f')
            #    self.updateTimeLastCall(timeLastUpdate)
            self._forceCallJson = True
        pass


    def getPathArchive(self):
        return self._path

    def setlastCallJson(self):
        import json
        data = {'timeLastCall':'%s'%self.getTimeLastCall(),
                'lastUpdate':'%s'%self.getLastUpdate(),
                'statutLastCall':self.getStatusLastCall(),
                #'timeLastUpdate':self.getTimeLastCall()
                }
        jsonData = json.dumps(data)
        self.setDataJson( "lastCall", data)

    def writeDataJson( self ):
        import json
        directory = "%s/" %(self.getPathArchive())
        for clef in self.getDataJsonKey():
            nomfichier = directory+clef+".json"
            data = self.getDataJson(clef)
            with open(nomfichier, 'w') as outfile:
                json.dump(data, outfile)

    def setDataJsonDefault(self, dataJsonDefault):
        self._dataJsonDefault = dataJsonDefault

    def setDataJsonCopy(self):
        self._dataJson = self._dataJsonDefault.copy()

    def getData(self):
        ##TEST
        #self.setDataJsonDefault({})
        #dataJson = self.readDataJson()
        #self.setDataJsonDefault(dataJsonDefault=dataJson)

        self.setDataJsonCopy()
        log.info(" >>>> getData, self._dataJson ? %s" %self._dataJson)
        if (self.getContract().getValue() == None):
            log.info("contract ? %s" %self.getContract().get_PDL_ID())
            try:
                self.updateContract()
                if ( self.getContract().getValue() != None ):
                    self.getContract().updateHCHP()
                log.info("contract ?(end) %s" %self.getContract().get_PDL_ID())
            except Exception as inst:
                log.error("myEnedis err %s" % (inst))
                log.error(traceback.format_exc())
                log.error("-" * 60)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.warning(sys.exc_info())
                self.updateStatusLastCall(False)
                self.updateTimeLastCall()
                self.updateErrorLastCall("%s" % (inst))
                log.error("LastMethodCall : %s" % (self.getLastMethodCall()))

        if (self.getContract().getValue() != None):
            self.update()
            self.setlastCallJson()
            self.writeDataJson()

        else:
            # on a eut un probleme lors de l'appel
            pass
        return True

    def getContract(self):
        return self._contract

    def isConsommation(self):
        return True #_consommation in self._contract["mode_PDL"]

    def isProduction(self):
        return True #_production in self._contract["mode_PDL"]

    def setDataJson(self, quoi, valeur ):
        self._dataJson[ quoi ] = valeur

    def getDataJson(self, quoi):
        return self._dataJson.get(quoi, None)

    def getDataJsonKey(self):
        return self._dataJson.keys()

    def updateContract(self, data=None):
        clefFunction = "updateContract"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data = self.getDataJson(clefFunction)
        data = self._contract.updateContract(data)
        self.setDataJson( clefFunction, data )

    def getYesterday(self):
        return self._yesterday

    def updateCurrentWeek(self, data=None):
        clefFunction = "updateCurrentWeek"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        firstdateofweek = (
                datetime.date.today() - datetime.timedelta(days=datetime.datetime.today().weekday() % 7)).strftime(
            _formatDateYmd)
        #if (cejour == firstdateofweek):
        #    return 0, False  # cas lundi = premier jour de la semaine et donc rien de dispo
        #else:
        #    return self.getDataPeriod(firstdateofweek, cejour)
        deb = self.getContract().minCompareDateContract(firstdateofweek)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._currentWeek.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._currentWeek.getNbCall() )

    def updateLastWeek(self, data=None):
        clefFunction = "updateLastWeek"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        start_date = today + datetime.timedelta(-today.weekday(), weeks=-1)
        end_date = today + datetime.timedelta(-today.weekday())
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._lastWeek.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._lastWeek.getNbCall() )

    def updateLast7Days(self, data=None):
        clefFunction = "updateLast7Days"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        start_date = today - datetime.timedelta(7)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._last7Days.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._last7Days.getNbCall() )

    def updateDataYesterdayHCHP(self, data=None, _yesterdayDate=None):
        clefFunction = "updateDataYesterdayHCHP"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, yesterdayDate = self.getDataJson(clefFunction), None
        if (_yesterdayDate != None): yesterdayDate = _yesterdayDate
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        #return self.getDataPeriodCLC(hier, cejour), hier
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._yesterdayHCHP.updateData(clefFunction, data, deb, fin)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._yesterdayHCHP.getNbCall() )

    def updateLast7DaysDetails(self, data=None, _yesterdayDate=None):
        clefFunction = "updateLast7DaysDetails"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, yesterdayDate = self.getDataJson(clefFunction), None
        today = datetime.date.today()
        start_date = today - datetime.timedelta(7)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        #return self.getDataPeriodCLC(start_date, end_date)
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._last7DaysDetails.updateData(clefFunction, data, deb, fin)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._last7DaysDetails.getNbCall() )

    def updateCurrentMonth(self, data=None):
        clefFunction = "updateCurrentMonth"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        debCurrentMonth = today.strftime(_formatDateYm01)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        #if (debCurrentMonth != cejour):
        #    return self.getDataPeriod(debCurrentMonth, cejour)
        #else:
        #    return 0, False
        deb = self.getContract().minCompareDateContract(debCurrentMonth)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._currentMonth.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._currentMonth.getNbCall() )

    def updateLastMonth(self, data=None):
        clefFunction = "updateLastMonth"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        import datetime
        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonth.strftime(_formatDateYm01)
        debCurrentMonth = first.strftime(_formatDateYm01)
        deb = self.getContract().minCompareDateContract(debPreviousMonth)
        fin = self.getContract().maxCompareDateContract(debCurrentMonth)
        data = self._lastMonth.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._lastMonth.getNbCall() )

    def updateLastMonthLastYear(self, data=None):
        clefFunction = "updateLastMonthLastYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        first = today.replace(day=1, year=today.year - 1)
        lastMonthLastYear = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonthLastYear.strftime(_formatDateYm01)
        debCurrentMonth = first.strftime(_formatDateYm01)
        deb = self.getContract().minCompareDateContract(debPreviousMonth)
        fin = self.getContract().maxCompareDateContract(debCurrentMonth)
        data = self._lastMonthLastYear.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._lastMonthLastYear.getNbCall() )

    def updateCurrentYear(self, data=None):
        clefFunction = "updateCurrentYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        debCurrentMonth = today.strftime(_formatDateY0101)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        #if (debCurrentMonth != cejour):
        #    return self.getDataPeriod(debCurrentMonth, cejour)
        #else:
        #    return 0, False
        deb = self.getContract().minCompareDateContract(debCurrentMonth)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._currentYear.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._currentYear.getNbCall() )

    def updateLastYear(self, data=None):
        clefFunction = "updateLastYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        first = today.replace(day=1, month=1)
        lastYear = first - datetime.timedelta(days=1)
        debPreviousYear = lastYear.strftime(_formatDateY0101)
        debCurrentYear = today.strftime(_formatDateY0101)
        deb = self.getContract().minCompareDateContract(debPreviousYear)
        fin = self.getContract().maxCompareDateContract(debCurrentYear)
        data = self._lastYear.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._lastYear.getNbCall() )

    def updateYesterdayLastYear(self, data=None):
        clefFunction = "updateYesterdayLastYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        todayLastYear = today.replace(year=today.year - 1)
        hier = (todayLastYear - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (todayLastYear).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._yesterdayLastYear.updateData(clefFunction, data, deb, fin)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._yesterdayLastYear.getNbCall() )

    def updateCurrentWeekLastYear(self, data=None):
        clefFunction = "updateCurrentWeekLastYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True

        today = datetime.date.today()
        numWeek = today.isocalendar()[1] # numero de la semaine
        previousYear = datetime.datetime.today().year - 1
        d = '%s-W%s'%(previousYear,numWeek)
        rfirstdateofweek = datetime.datetime.strptime(d + '-1', '%G-W%V-%u')
        # on recule d'un jour, car on a pas les données du jours, vs on a celle de l'an passé
        r = rfirstdateofweek + datetime.timedelta(days=datetime.datetime.today().weekday() ) # car on a pas les données du jour...
        cejour = r.strftime(_formatDateYmd)
        r = rfirstdateofweek + datetime.timedelta(
            days=datetime.datetime.today().weekday())  # car on a pas les données du jour...
        cejourmoins1 = r.strftime(_formatDateYmd)

        firstdateofweek = rfirstdateofweek.strftime(_formatDateYmd)
        #if (cejour == firstdateofweek) or ( firstdateofweek > cejour ):
        #    return 0, False  # cas lundi = premier jour de la semaine et donc rien de dispo
        #else:
        #    return self.getDataPeriod(firstdateofweek, cejourmoins1)
        deb = self.getContract().minCompareDateContract(firstdateofweek)
        fin = self.getContract().maxCompareDateContract(cejourmoins1)
        data = self._currentWeekLastYear.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._currentWeekLastYear.getNbCall() )

    def updateCurrentMonthLastYear(self, data=None):
        clefFunction = "updateCurrentMonthLastYear"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        today = today.replace(year=datetime.date.today().year - 1)
        debCurrentMonthPreviousYear = today.strftime(_formatDateYm01)
        cejourPreviousYear = datetime.date.today()
        cejourPreviousYear = cejourPreviousYear.replace(year=datetime.date.today().year - 1)
        #cejourPreviousYear = cejourPreviousYear - datetime.timedelta(1)
        cejourPreviousYear = cejourPreviousYear.strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(debCurrentMonthPreviousYear)
        fin = self.getContract().maxCompareDateContract(cejourPreviousYear)
        data = self._currentMonthLastYear.updateData(clefFunction, data, deb, fin, withControl=True)
        self.setDataJson(clefFunction, data)
        self.setNbCall( self._currentMonthLastYear.getNbCall() )

    def updateYesterday(self, data=None):
        clefFunction = "updateYesterday"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        #print("data :", data)
        data = self._yesterday.updateData(clefFunction, data, deb, fin)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._yesterday.getNbCall() )

    def updateYesterdayProduction(self, data=None):
        clefFunction = "updateYesterdayProduction"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._productionYesterday.updateData(clefFunction, data, deb, fin)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._productionYesterday.getNbCall() )

    def updateYesterdayConsumptionMaxPower(self, data=None):
        clefFunction = "updateYesterdayConsumptionMaxPower"
        self.updateLastMethodCall(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        #val1, val2 = self.getDataPeriodConsumptionMaxPower(hier, cejour)
        data = self._yesterdayConsumptionMaxPower.updateData(clefFunction, data, deb, fin)
        self.setDataJson( clefFunction, data )
        self.setNbCall( self._yesterdayConsumptionMaxPower.getNbCall() )

    def getYesterdayLastYear(self):
        return self._yesterdayLastYear

    def getYesterdayConsumptionMaxPower(self):
        return self._yesterdayConsumptionMaxPower

    def getProductionYesterday(self):
        return self._productionYesterday

    def getYesterdayHCHP(self):
        return self._yesterdayHCHP

    def getHCCost(self, val):
        return val * self._heuresCreusesCost  # car à l'heure et non à la demi-heure

    def getHPCost(self, val):
        return val * self._heuresPleinesCost  # car à l'heure et non à la demi-heure

    def getLastMonth(self):
        return self._lastMonth

    def getLastMonthLastYear(self):
        return self._lastMonthLastYear

    def getLastWeek(self):
        return self._lastWeek

    def getLast7Days(self):
        return self._last7Days

    def getLast7DaysDetails(self):
        return self._last7DaysDetails

    def getCurrentWeek(self):
        return self._currentWeek

    def getCurrentWeekLastYear(self):
        return self._currentWeekLastYear

    def getCurrentMonthLastYear(self):
        return self._currentMonthLastYear

    def getCurrentMonth(self):
        return self._currentMonth

    def CallgetCurrentMonthDetails(self):
        import datetime
        today = datetime.date.today()
        debCurrentMonth = today.strftime(_formatDateYm01)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        if (debCurrentMonth != cejour):
            return self.getDataPeriodCLC(debCurrentMonth, cejour)
        else:
            return 0

    def getLastYear(self):
        return self._lastYear

    def getCurrentYear(self):
        return self._currentYear

    def getLastUpdate(self):
        return self._lastUpdate

    def updateLastUpdate(self, t = datetime.datetime.now()):
        self._lastUpdate = t

    def getTimeLastCall(self):
        return self._timeLastUpdate

    def updateTimeLastCall(self, t = datetime.datetime.now() ):
        if ( not self._forceCallJson ):
            self._timeLastUpdate = t

    def getStatusLastCall(self):
        return self._statusLastCall

    def getNbCall(self):
        return self._nbCall

    def setNbCall(self, nbCall):
        self._nbCall += nbCall

    def updateStatusLastCall(self, status):
        self._statusLastCall = status

    def getErrorLastCall(self):
        return self._errorLastCall

    def getCardErrorLastCall(self):
        if ( myCalli.getLastAnswer() != None):
            if ( "alert_user" in myCalli.getLastAnswer()):
                if ( myCalli.getLastAnswer()["alert_user"]):
                    if ( "description" in myCalli.getLastAnswer()
                        and "tag" in myCalli.getLastAnswer()):
                        # si erreur autre que mauvais sens de lecture...
                        if ( myCalli.getLastAnswer()["error_code"] != "ADAM-ERR0069" ):
                            return "%s (%s-%s)" %(myCalli.getLastAnswer()["description"], myCalli.getLastAnswer()["error_code"], myCalli.getLastAnswer()["tag"])
                        else:
                            return ""
                    else:
                        return self.getErrorLastCall()
                else:
                    return ""
            else:
                return self.getErrorLastCall()
        else:
            return ""

    def getLastMethodCall(self):
        return self._errorLastMethodCall

    def getLastMethodCallError(self):
        return self._errorLastMethodCallError

    def updateLastMethodCall(self, methodName):
        self._errorLastMethodCall = methodName
        if (self._errorLastMethodCallError == self._errorLastMethodCall):
            self._errorLastMethodCallError = ""
            self.updateStatusLastCall(True)  # pour la prochaine reprenne normalement car tout est conforme

    def updateLastMethodCallError(self, methodName):
        self._errorLastMethodCallError = methodName

    def updateErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def setErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def getDelaiError(self):
        return self._delai

    def getDelaiIsGoodAfterError(self, currentDateTime):
        log.info("TimeLastCall : %s" % (self.getTimeLastCall()))
        ecartOk = True
        if ( self.getTimeLastCall() != None ):
            ecartOk = ( currentDateTime - self.getTimeLastCall()).total_seconds() > self.getDelaiError()
        return ecartOk

    def getHorairePossible(self):
        # hier 23h
        hourNow = datetime.datetime.now().hour
        log.info("now : %s" % (hourNow))
        horairePossible = ( hourNow >= 10 ) and ( hourNow < 23 )
        # for test
        #horairePossible = ( hourNow >= 11 ) and ( hourNow < 23 )
        log.info("horairePossible : %s" % (horairePossible))
        return horairePossible

    def getLastCallHier(self):
        if ( self.getTimeLastCall() != None ):
            hier = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(hour=23,minute=40)
            lastCall = self.getTimeLastCall()
            lastCallHier = (lastCall < hier)
        else:
            lastCallHier = False
        ## TESTR
        #lastCallHier = True
        return lastCallHier

    def updateGitVersion(self):
        gitInfo = gitinformation.gitinformation("saniho/apiEnedis")
        gitInfo.getInformation()
        self._gitVersion = gitInfo.getVersion()

    def getCallPossible(self, currentDateTime = datetime.datetime.now()):
        log.info("myEnedis ...new update self.getHorairePossible() : %s ??" %self.getHorairePossible())
        log.info("myEnedis ...new update self.getLastCallHier() : %s ??" %self.getLastCallHier())
        log.info("myEnedis ...new update self.getTimeLastCall() : %s ??" %self.getTimeLastCall())
        log.info("myEnedis ...new update self.getStatusLastCall() : %s??" %self.getStatusLastCall())
        log.info("myEnedis ...new update self.getDelaiIsGoodAfterError() : %s??" %self.getDelaiIsGoodAfterError(currentDateTime))
        # new callpossible ???
        callpossible = ( self.getHorairePossible() and
                         ( self.getLastCallHier() or (self.getTimeLastCall() == None) or
                           (self.getStatusLastCall() == False and self.getDelaiIsGoodAfterError(currentDateTime))
                         )
                        )
        log.info("myEnedis ..._forceCallJson : %s??" % self._forceCallJson )
        if ( self._forceCallJson ):
            callpossible = True
        return callpossible

    def getGitVersion(self):
        return self._gitVersion

    def update(self):
        #log.info("myEnedis ...new update ??" )

        if (self.getContract().getValue() != None):
            if self.getCallPossible():
                try:
                    log.error("myEnedis ...%s update lancé, status precedent : %s, lastCall :%s" \
                                      % (self.getContract().get_PDL_ID(), self.getStatusLastCall(), self.getLastMethodCallError()))
                    self._nbCall = 0
                    self.updateGitVersion()
                    self.updateErrorLastCall("")
                    self.updateLastMethodCall("")
                    self.setUpdateRealise(True)
                    try:
                        if (self.isConsommation()):
                            self._niemeAppel += 1
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateYesterday"):
                                self.updateYesterday()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentWeek"):
                                self.updateCurrentWeek()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastWeek"):
                                self.updateLastWeek()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLast7Days"):
                                self.updateLast7Days()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateDataYesterdayHCHP"):
                                self.updateDataYesterdayHCHP()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLast7DaysDetails"):
                                self.updateLast7DaysDetails()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentMonth"):
                                self.updateCurrentMonth()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastMonth"):
                                self.updateLastMonth()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastMonthLastYear"):
                                self.updateLastMonthLastYear()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentYear"):
                                self.updateCurrentYear()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastYear"):
                                self.updateLastYear()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateYesterdayLastYear"):
                                self.updateYesterdayLastYear()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentWeekLastYear"):
                                self.updateCurrentWeekLastYear()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateYesterdayConsumptionMaxPower"):
                                self.updateYesterdayConsumptionMaxPower()
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentMonthLastYear"):
                                self.updateCurrentMonthLastYear()

                            self.updateTimeLastCall()
                            self.updateStatusLastCall(True)
                            log.info("mise à jour effectuee consommation")

                        if (self.isProduction()):
                            if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateYesterdayProduction"):
                                self.updateYesterdayProduction()
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(True)
                            log.info("mise à jour effectuee production")
                        if ( self._forceCallJson ):
                            self._forceCallJson = False
                            self.setDataJsonDefault({})

                        log.error("myEnedis ...%s update termine, status courant : %s, lastCall :%s, nbCall :%s" \
                              % (self.getContract().get_PDL_ID(), self.getStatusLastCall(), self.getLastMethodCallError(),
                                 self.getNbCall()))

                    except Exception as inst:
                        if (inst.args[:2] == (
                        "call", "error")):  # gestion que c'est pas une erreur de contrat trop recent ?
                            log.error("%s - Erreur call ERROR %s" % (self.getContract().get_PDL_ID(), inst))
                            # Erreur lors du call...
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self.updateErrorLastCall(
                                "%s - %s" % (messages.getMessage(inst.args[2]), myCalli.getLastAnswer()))
                            log.error(
                                "%s - last call : %s" % (self.getContract().get_PDL_ID(), self.getLastMethodCall()))
                        else:
                            raise Exception(inst)

                except Exception as inst:
                    if (inst.args == ("call", None)):
                        log.error("*" * 60)
                        log.error("%s - Erreur call" % (self.getContract().get_PDL_ID(),))
                        self.updateTimeLastCall()
                        self.updateStatusLastCall(False)
                        message = "%s - %s" % (messages.getMessage(inst.args[2]), myCalli.getLastAnswer())
                        self.updateErrorLastCall(message)
                        log.error("%s - %s" % (self.getContract().get_PDL_ID(), self.getLastMethodCall()))
                    else:
                        log.error("-" * 60)
                        log.error("Erreur inconnue call ERROR %s" % (inst))
                        log.error("Erreur last answer %s" % (inst))
                        log.error("Erreur last call %s" % (self.getLastMethodCall()))
                        log.error(traceback.format_exc())
                        log.error("-" * 60)
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        log.warning(sys.exc_info())
                        self.updateStatusLastCall(False)
                        self.updateTimeLastCall()
                        self.updateErrorLastCall("%s" % (inst))
                        log.error("LastMethodCall : %s" % (self.getLastMethodCall()))
            else:
                self.setUpdateRealise(False)
                #log.info("%s pas d'update trop tot !!!" % (self.getContract().get_PDL_ID()))
        else:
            self.setUpdateRealise(False)
            log.info("%s update impossible contrat non trouve!!!" % (self.getContract().get_PDL_ID()))
        self.updateLastUpdate()
