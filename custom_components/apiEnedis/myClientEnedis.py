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
        self._myCalli = myCall()
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

        import random
        self._horaireMin = datetime.datetime(2021,7,21,9,30) + datetime.timedelta(minutes=random.randrange(90))

        self._myCalli.setParam( PDL_ID, token, version)
        self._contract = myContrat( self._myCalli, self._token, self._PDL_ID, self._version, heuresCreusesON, heuresCreuses)
        self._yesterday = myDataEnedis( self._myCalli, self._token, self._version, self._contract)
        self._yesterdayLastYear = myDataEnedis( self._myCalli, self._token, self._version, self._contract)
        self._currentWeek = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._currentWeekLastYear = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._lastWeek = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._last7Days = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._currentMonth = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._currentMonthLastYear = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._lastMonth = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._lastMonthLastYear = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._currentYear = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._lastYear = myDataEnedisByDay( self._myCalli, self._token, self._version, self._contract)
        self._yesterdayHCHP = myDataEnedisByDayDetail( self._myCalli, self._token, self._version, self._contract)
        self._last7DaysDetails = myDataEnedisByDayDetail( self._myCalli, self._token, self._version, self._contract, True)

        self._productionYesterday = myDataEnedisProduction( self._myCalli, self._token, self._version, self._contract)

        self._yesterdayConsumptionMaxPower = myDataEnedisMaxPower( self._myCalli, self._token, self._version, self._contract)
        log.info("run myEnedis")
        self._gitVersion = None
        self._dataJsonDefault = {}
        self._dataJson = {}
        pass

    def getVersion(self):
        return self._version

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
        log.info("%s - %s - fichier lu dataRepertoire : %s" %(self.getContract().get_PDL_ID(), self._PDL_ID, dataRepertoire ))
        directory = "%s/*.json" %dataRepertoire
        log.info("fichier lu directory : %s" %directory )
        listeFile = glob.glob(directory)
        log.info("fichier lu listeFile : %s" %listeFile )
        for nomFichier in listeFile:
            try:
                with open(nomFichier) as json_file:
                    clef = os.path.basename(nomFichier).split(".")[0]
                    data[clef] = json.load(json_file)
            except:
                log.error(" >>>> erreur lecture : %s" %(nomFichier))
                pass # si erreur lecture ... on continue ;)
        return data

    def manageLastCallJson(self):
        lastCallInformation = self.getDataJson("lastCall")
        log.info("manageLastCallJson : ")
        if ( lastCallInformation != None):
            try:
                self._forceCallJson = True
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
                version = lastCallInformation.get("version", None)
                log.info("manageLastCallJson : previous version : %s" %version)
            except:
                # si le fichier est mal formaté
                pass
        pass


    def getPathArchive(self):
        return self._path

    def setlastCallJson(self):
        import json
        data = {'timeLastCall':'%s'%self.getTimeLastCall(),
                'lastUpdate':'%s'%self.getLastUpdate(),
                'statutLastCall':self.getStatusLastCall(),
                'version':self.getVersion(),
                #'timeLastUpdate':self.getTimeLastCall()
                }
        jsonData = json.dumps(data)
        self.setDataJson( "lastCall", data)

    def writeDataJson( self ):
        import json
        directory = "%s/" %(self.getPathArchive())
        for clef in self.getDataJsonKey():
            try:
                data = {}
                nomfichier = directory+clef+".json"
                data = self.getDataJson(clef)
                log.info(" >>>> ecriture : %s / %s" %(nomfichier, data))
                with open(nomfichier, 'w') as outfile:
                    json.dump(data, outfile)
            except:
                log.error(" >>>> erreur ecriture : %s / %s" %(nomfichier, data))

    def setDataJsonDefault(self, dataJsonDefault):
        self._dataJsonDefault = dataJsonDefault

    def setDataJsonCopy(self):
        self._dataJson = self._dataJsonDefault.copy()

    def getData(self):
        ### A VOIR ###
        ## supprimer test ecrire sur ok present ou non !!! pas d'interet
        #self.setDataJsonCopy() # pourquoi cela ? vu qu'on l'a mis juste avant ... pas besoin du default !!!!
        log.info(" %s >>>> getData, self._dataJson ? %s" %( self._PDL_ID, self._dataJson))
        if (self.getContract().getValue() == None):
            log.info("contract ? %s" %self.getContract().get_PDL_ID())
            try:
                if self.getCallPossible():
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
            log.info("UpdateRealise : %s" % (self.getUpdateRealise()))
            if ( self.getUpdateRealise()):
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

    def setDataRequestJson(self, quoi, myObjet ):
        quoi = "%s_Req" %quoi
        self._dataJson[ quoi ] = { 'deb' : myObjet.getDateDeb(), 'fin' : myObjet.getDateFin(), "callok" : myObjet.getCallOk() }

    def getDataRequestJson(self, quoi):
        quoi = "%s_Req" %quoi
        request = self._dataJson.get(quoi, {})
        return request

    def getDataJsonKey(self):
        return self._dataJson.keys()

    def updateContract(self, data=None):
        clefFunction = "updateContract"
        self.updateLastMethodCall(clefFunction)
        log.info("%s - updatecontract data : %s" %(self._PDL_ID, data))
        if (data == None): data = self.getDataJson(clefFunction)
        log.info("%s - updatecontract data : %s" %(self._PDL_ID, data))
        data = self._contract.updateContract(data)
        self.setDataJson( clefFunction, data )

    def getYesterday(self):
        return self._yesterday

    def updateCurrentWeek(self, data=None, withControl=True):
        clefFunction = "updateCurrentWeek"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
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
        data = self._currentWeek.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl=requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._currentWeek )
        self.setNbCall( self._currentWeek.getNbCall() )

    def updateLastWeek(self, data=None, withControl=True):
        clefFunction = "updateLastWeek"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        start_date = (today + datetime.timedelta(-today.weekday(), weeks=-1)).strftime(_formatDateYmd)
        end_date = (today + datetime.timedelta(-today.weekday())).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._lastWeek.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl=requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._lastWeek )
        self.setNbCall( self._lastWeek.getNbCall() )

    def updateLast7Days(self, data=None, withControl=True):
        clefFunction = "updateLast7Days"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._last7Days.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl=requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._last7Days )
        self.setNbCall( self._last7Days.getNbCall() )

    def updateDataYesterdayHCHP(self, data=None, _yesterdayDate=None, withControl=True):
        clefFunction = "updateDataYesterdayHCHP"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, yesterdayDate = self.getDataJson(clefFunction), None
        if (_yesterdayDate != None): yesterdayDate = _yesterdayDate
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        #return self.getDataPeriodCLC(hier, cejour), hier
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._yesterdayHCHP.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl=requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._yesterdayHCHP )
        self.setNbCall( self._yesterdayHCHP.getNbCall() )

    def updateLast7DaysDetails(self, data=None, _yesterdayDate=None, withControl=True):
        clefFunction = "updateLast7DaysDetails"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, yesterdayDate = self.getDataJson(clefFunction), None
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(start_date)
        fin = self.getContract().maxCompareDateContract(end_date)
        data = self._last7DaysDetails.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._last7DaysDetails )
        self.setNbCall( self._last7DaysDetails.getNbCall() )

    def updateCurrentMonth(self, data=None, withControl=True):
        clefFunction = "updateCurrentMonth"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
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
        data = self._currentMonth.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._currentMonth )
        self.setNbCall( self._currentMonth.getNbCall() )

    def updateLastMonth(self, data=None, withControl=True):
        clefFunction = "updateLastMonth"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        import datetime
        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonth.strftime(_formatDateYm01)
        debCurrentMonth = first.strftime(_formatDateYm01)
        deb = self.getContract().minCompareDateContract(debPreviousMonth)
        fin = self.getContract().maxCompareDateContract(debCurrentMonth)
        data = self._lastMonth.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._lastMonth )
        self.setNbCall( self._lastMonth.getNbCall() )

    def updateLastMonthLastYear(self, data=None, withControl=True):
        clefFunction = "updateLastMonthLastYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        first = today.replace(day=1, year=today.year - 1)
        lastMonthLastYear = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonthLastYear.strftime(_formatDateYm01)
        debCurrentMonth = first.strftime(_formatDateYm01)
        deb = self.getContract().minCompareDateContract(debPreviousMonth)
        fin = self.getContract().maxCompareDateContract(debCurrentMonth)
        data = self._lastMonthLastYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._lastMonthLastYear )
        self.setNbCall( self._lastMonthLastYear.getNbCall() )

    def updateCurrentYear(self, data=None, withControl=True):
        clefFunction = "updateCurrentYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        debCurrentMonth = today.strftime(_formatDateY0101)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(debCurrentMonth)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._currentYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._currentYear )
        self.setNbCall( self._currentYear.getNbCall() )

    def updateLastYear(self, data=None, withControl=True):
        clefFunction = "updateLastYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        first = today.replace(day=1, month=1)
        lastYear = first - datetime.timedelta(days=1)
        debPreviousYear = lastYear.strftime(_formatDateY0101)
        debCurrentYear = today.strftime(_formatDateY0101)
        deb = self.getContract().minCompareDateContract(debPreviousYear)
        fin = self.getContract().maxCompareDateContract(debCurrentYear)
        data = self._lastYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._lastYear )
        self.setNbCall( self._lastYear.getNbCall() )

    def updateYesterdayLastYear(self, data=None, withControl=True):
        clefFunction = "updateYesterdayLastYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        todayLastYear = today.replace(year=today.year - 1)
        hier = (todayLastYear - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (todayLastYear).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._yesterdayLastYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._yesterdayLastYear )
        self.setNbCall( self._yesterdayLastYear.getNbCall() )

    def updateCurrentWeekLastYear(self, data=None, withControl=True):
        clefFunction = "updateCurrentWeekLastYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
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
        data = self._currentWeekLastYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._currentWeekLastYear )
        self.setNbCall( self._currentWeekLastYear.getNbCall() )

    def updateCurrentMonthLastYear(self, data=None, withControl=True):
        clefFunction = "updateCurrentMonthLastYear"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        today = datetime.date.today()
        today = today.replace(year=datetime.date.today().year - 1)
        debCurrentMonthPreviousYear = today.strftime(_formatDateYm01)
        cejourPreviousYear = datetime.date.today()
        cejourPreviousYear = cejourPreviousYear.replace(year=datetime.date.today().year - 1)
        cejourPreviousYear = cejourPreviousYear.strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(debCurrentMonthPreviousYear)
        fin = self.getContract().maxCompareDateContract(cejourPreviousYear)
        data = self._currentMonthLastYear.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson(clefFunction, data)
        self.setDataRequestJson( clefFunction, self._currentMonthLastYear )
        self.setNbCall( self._currentMonthLastYear.getNbCall() )

    def updateYesterday(self, data=None, withControl=True):
        clefFunction = "updateYesterday"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        #print("data :", data)
        data = self._yesterday.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._yesterday )
        self.setNbCall( self._yesterday.getNbCall() )

    def updateYesterdayProduction(self, data=None, withControl=True):
        clefFunction = "updateYesterdayProduction"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        data = self._productionYesterday.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._productionYesterday )
        self.setNbCall( self._productionYesterday.getNbCall() )

    def updateYesterdayConsumptionMaxPower(self, data=None, withControl=True):
        clefFunction = "updateYesterdayConsumptionMaxPower"
        self.updateLastMethodCall(clefFunction)
        requestJson = self.getDataRequestJson(clefFunction)
        if (data == None): data, callDone = self.getDataJson(clefFunction), True
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.getContract().minCompareDateContract(hier)
        fin = self.getContract().maxCompareDateContract(cejour)
        #val1, val2 = self.getDataPeriodConsumptionMaxPower(hier, cejour)
        data = self._yesterdayConsumptionMaxPower.updateData(clefFunction, self.getHorairePossible(), data, deb, fin, withControl=withControl, dataControl = requestJson)
        self.setDataJson( clefFunction, data )
        self.setDataRequestJson( clefFunction, self._yesterdayConsumptionMaxPower )
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

    def updateTimeLastCall(self, t = None):
        if ( t is None ):
            t = datetime.datetime.now()
            self._timeLastUpdate = t
        else:
            self._timeLastUpdate = t

    def getStatusLastCall(self):
        return self._statusLastCall

    def getNbCall(self):
        return self._nbCall

    def setNbCall(self, nbCall):
        self._nbCall += nbCall

    def updateStatusLastCall(self, status):
        if ( not self._forceCallJson ): # pour eviter d'ecraser le statut quand on recupere la date depuis le json
            self._statusLastCall = status

    def getErrorLastCall(self):
        return self._errorLastCall

    def getCardErrorLastCall(self):
        if (self._myCalli.getLastAnswer() == None):               return ""
        if ("alert_user" not in self._myCalli.getLastAnswer()):   return self.getErrorLastCall()
        if (not self._myCalli.getLastAnswer()["alert_user"]):     return ""
        if ("description" in self._myCalli.getLastAnswer() and "tag" in self._myCalli.getLastAnswer()):
            # si erreur autre que mauvais sens de lecture...
            if (self._myCalli.getLastAnswer()["error_code"] == "ADAM-ERR0069"):
                return ""
            else:
                return "%s (%s-%s)" % (
                self._myCalli.getLastAnswer()["description"], self._myCalli.getLastAnswer()["error_code"],
                self._myCalli.getLastAnswer()["tag"])
        else:
            return self.getErrorLastCall()

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
        #test
        #ecartOk = True
        return ecartOk

    def getHoraireMin(self):
        return self._horaireMin.hour *100 + self._horaireMin.minute

    def getHorairePossible(self):
        # hier 23h
        hourNow = datetime.datetime.now().hour * 100 + datetime.datetime.now().minute
        log.info("now : %s" %hourNow)
        horairePossible = ( hourNow >= self.getHoraireMin() ) and ( hourNow < 2330 )
        log.info("now : %s" %self.getHoraireMin())
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

    def getCallPossible(self, currentDateTime = datetime.datetime.now(), trace = False):
        # new callpossible ???
        callpossible = ( self.getHorairePossible() and
                            ( self.getLastCallHier() or
                                ( self.getTimeLastCall() == None) or
                                ( self.getStatusLastCall() == False
                                  and self.getDelaiIsGoodAfterError(currentDateTime)
                                )
                            )
                        )
        #if ( self.getDelaiIsGoodAfterError(currentDateTime) ):
        #    trace = True # pour activer la trace ... et voir comprendre quelque choose
        #if ( self.getStatusLastCall() == False ):
        #    trace = True # pour activer la trace ... et voir comprendre quelque choose
        if ( self._forceCallJson ):
            callpossible = True
        if ( trace ):
            log.error("myEnedis ...new update self.getHorairePossible() : %s ??" %self.getHorairePossible())
            log.error("myEnedis ...new update self.getLastCallHier() : %s ??" %self.getLastCallHier())
            log.error("myEnedis ...new update self.getTimeLastCall() : %s ??" %self.getTimeLastCall())
            log.error("myEnedis ...new update self.getStatusLastCall() : %s??" %self.getStatusLastCall())
            log.error("myEnedis ...new update self.getDelaiIsGoodAfterError() : %s??" %self.getDelaiIsGoodAfterError(currentDateTime))
            log.error("myEnedis ..._forceCallJson : %s??" % self._forceCallJson )
            log.error("myEnedis ...<< call Possible >> : %s??" % callpossible)
        else:
            log.info("myEnedis ...new update self.getHorairePossible() : %s ??" %self.getHorairePossible())
            log.info("myEnedis ...new update self.getLastCallHier() : %s ??" %self.getLastCallHier())
            log.info("myEnedis ...new update self.getTimeLastCall() : %s ??" %self.getTimeLastCall())
            log.info("myEnedis ...new update self.getStatusLastCall() : %s??" %self.getStatusLastCall())
            log.info("myEnedis ...new update self.getDelaiIsGoodAfterError() : %s??" %self.getDelaiIsGoodAfterError(currentDateTime))
            log.info("myEnedis ..._forceCallJson : %s??" % self._forceCallJson )
            log.info("myEnedis ...<< call Possible >> : %s??" % callpossible)
        return callpossible

    def getGitVersion(self):
        return self._gitVersion

    def update(self):
        log.info("myEnedis ...new update ?? %s"%self._PDL_ID )
        if (self.getContract().getValue() != None):
            if self.getCallPossible():
                try:
                    log.info("myEnedis(%s) ...%s update lancé, status precedent : %s, lastMethodCall :%s, forcejson :%s" \
                        % (self.getVersion(), self.getContract().get_PDL_ID(),
                           self.getStatusLastCall(), self.getLastMethodCallError(),
                        self._forceCallJson))
                    log.error("myEnedis(%s) ...%s update lancé, status precedent : %s, lastMethodCall :%s, forcejson :%s" \
                        % (self.getVersion(), self.getContract().get_PDL_ID(),
                           self.getStatusLastCall(), self.getLastMethodCallError(),
                           self._forceCallJson))
                    #self.getCallPossible()
                    self._nbCall = 0
                    self.updateGitVersion()
                    self.updateErrorLastCall("")
                    self.updateLastMethodCall("")
                    self.setUpdateRealise(True)
                    if ( not self._forceCallJson ) : # si pas un forcage alors on reset le last call...
                        self.updateStatusLastCall(True)
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

                        log.error("myEnedis(%s) ...%s update termine, status courant : %s, lastCall :%s, nbCall :%s" \
                              % (
                                self.getVersion(), self.getContract().get_PDL_ID(),
                                self.getStatusLastCall(), self.getLastMethodCallError(),
                                self.getNbCall()))
                        log.info("myEnedis(%s) ...%s update termine, status courant : %s, lastCall :%s, nbCall :%s" \
                              % (
                                self.getVersion(), self.getContract().get_PDL_ID(),
                                self.getStatusLastCall(), self.getLastMethodCallError(),
                                self.getNbCall()))
                    except Exception as inst:
                        # pour eviter de boucler le call en permanence
                        if ( self._forceCallJson ):
                            self._forceCallJson = False
                            self.setDataJsonDefault({})
                        if (inst.args[:2] == ("call", "error")):  # gestion que c'est pas une erreur de contrat trop recent ?
                            log.error("%s - Erreur call ERROR %s" % (self.getContract().get_PDL_ID(), inst))
                            # Erreur lors du call...
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self.updateErrorLastCall(
                                "%s - %s" % (messages.getMessage(inst.args[2]), self._myCalli.getLastAnswer()))
                            log.error(
                                "%s - last call : %s" % (self.getContract().get_PDL_ID(), self.getLastMethodCall()))
                            log.error("myEnedis ...%s update termine, on retentera plus tard(A)" % (self.getContract().get_PDL_ID()))
                        else:
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self.updateErrorLastCall("%s" % (self._myCalli.getLastAnswer()))
                            log.error(
                                "%s - last call : %s" % (self.getContract().get_PDL_ID(), self.getLastMethodCall()))
                            log.error("myEnedis ...%s update termine, on retentera plus tard(B)" % (self.getContract().get_PDL_ID()))
                            raise Exception(inst)

                except Exception as inst:
                    if (inst.args == ("call", None)):
                        log.error("*" * 60)
                        log.error("%s - Erreur call" % (self.getContract().get_PDL_ID(),))
                        self.updateTimeLastCall()
                        self.updateStatusLastCall(False)
                        message = "%s - %s" % (messages.getMessage(inst.args[2]), self._myCalli.getLastAnswer())
                        self.updateErrorLastCall(message)
                        log.error("%s - %s" % (self.getContract().get_PDL_ID(), self.getLastMethodCall()))
                    else:
                        log.error("-" * 60)
                        log.error("Erreur inconnue call ERROR %s" % (inst))
                        log.error("Erreur last answer %s" % (inst))
                        log.error("Erreur last call %s" % (self.getLastMethodCall()))
                        log.error("Erreur last answer %s" % (self._myCalli.getLastAnswer()))
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
        return True
