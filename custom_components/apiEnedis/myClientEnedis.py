from __future__ import annotations

import datetime
import logging
import sys
import traceback
from typing import Any

try:
    from .const import (  # isort:skip
        __nameMyEnedis__,
        _formatDateYmd,
        _ENEDIS_MyElectricData,
    )
    from . import messages

except ImportError:
    import messages  # type: ignore[no-redef]
    from const import (  # type: ignore[no-redef]
        __nameMyEnedis__,
        _formatDateYmd,
    )

from . import apiconst as API
from .myCall import myCall
from .myContrat import myContrat
from .myDataEnedis import myDataEnedis
from .myDataEnedisByDay import myDataEnedisByDay
from .myDataEnedisByDayDetail import myDataEnedisByDayDetail
from .myDataEnedisMaxPower import myDataEnedisMaxPower
from .myDataEnedisProduction import myDataEnedisProduction
from .myDataEnedisEcoWatt import myDataEnedisEcoWatt
from .myDataEnedisTempo import myDataEnedisTempo

log = logging.getLogger(__nameMyEnedis__)


class myClientEnedis:
    def __init__(
        self,
        token: str,
        PDL_ID: str,
        delay: int = 3600,
        heuresCreuses=None,
        heuresCreusesCost: float = 0,
        heuresPleinesCost: float = 0,
        version: str = "0.0.0",
        heuresCreusesON: bool = True,
        serviceEnedis: str = "enedisGateway"
    ):
        self._myCalli = myCall()
        self._token: str = token
        self._PDL_ID: str = PDL_ID
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall: bool = True
        self._errorLastCall = None
        self._lastMethodCall: str = ""
        self._lastMethodCallError = None
        self._delay = delay
        self._heuresCreusesCost: float = heuresCreusesCost
        self._heuresPleinesCost: float = heuresPleinesCost
        self._updateRealise: bool = False
        self._nbCall: int = 0
        self._niemeAppel: int = 0
        self._version: str = version
        self._forceCallJson: bool = False
        self._path: str | None = None
        self._serviceEnedis: str = serviceEnedis

        import random

        self._horaireMin = datetime.datetime(2021, 7, 21, 9, 30) + datetime.timedelta(
            minutes=random.randrange(360)
        )

        self._myCalli.setParam(PDL_ID, token, version, serviceEnedis)
        self.contract = myContrat(
            self._myCalli,
            self._token,
            self._PDL_ID,
            self._version,
            heuresCreusesON,
            heuresCreuses,
        )
        self._yesterday = myDataEnedis(
            self._myCalli, self._token, self._version, self.contract
        )
        self._yesterdayLastYear = myDataEnedis(
            self._myCalli, self._token, self._version, self.contract
        )
        self._currentWeek = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._currentWeekLastYear = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._lastWeek = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._last7Days = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._currentMonth = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._currentMonthLastYear = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._lastMonth = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._lastMonthLastYear = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._currentYear = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._lastYear = myDataEnedisByDay(
            self._myCalli, self._token, self._version, self.contract
        )
        self._yesterdayHCHP = myDataEnedisByDayDetail(
            self._myCalli, self._token, self._version, self.contract
        )
        self._last7DaysDetails = myDataEnedisByDayDetail(
            self._myCalli, self._token, self._version, self.contract, True
        )

        self._productionYesterday = myDataEnedisProduction(
            self._myCalli, self._token, self._version, self.contract
        )

        self._yesterdayConsumptionMaxPower = myDataEnedisMaxPower(
            self._myCalli, self._token, self._version, self.contract
        )

        self._ecoWatt = myDataEnedisEcoWatt(
            self._myCalli, self._token, self._version, self.contract
        )

        self._tempo = myDataEnedisTempo(
            self._myCalli, self._token, self._version, self.contract
        )

        log.info("run myEnedis")
        self._gitVersion: str | None = None
        self._dataJsonDefault: dict[str, Any] = {}
        self._dataJson: dict[str, Any] = {}

    def getVersion(self) -> str:
        return self._version

    def setUpdateRealise(self, value: bool):
        self._updateRealise = value

    def getUpdateRealise(self) -> bool:
        return self._updateRealise

    def setPathArchive(self, path: str):
        self._path = path

    def getServiceEnedis(self):
        return self._serviceEnedis

    def readDataJson(self):
        import glob
        import json
        import os

        data = {}
        dataRepertoire = self.getPathArchive()
        log.info(
            "%s - %s - fichier lu dataRepertoire : %s",
            self.contract.get_PDL_ID(),
            self._PDL_ID,
            dataRepertoire,
        )
        directory = f"{dataRepertoire}/*.json"
        log.info(f"fichier lu directory : {directory}")
        listeFile = glob.glob(directory)
        log.info(f"fichier lu listeFile : {listeFile}")
        for nomFichier in listeFile:
            try:
                with open(nomFichier) as json_file:
                    clef = os.path.basename(nomFichier).split(".")[0]
                    data[clef] = json.load(json_file)
            except:
                log.error(f" >>>> erreur lecture : {nomFichier}")
                pass  # si erreur lecture ... on continue ;)
        return data

    def manageLastCallJson(self):
        lastCallInformation = self.getDataJsonValue("lastCall")
        log.info("manageLastCallJson : ")
        if lastCallInformation is not None:
            try:
                self._forceCallJson = True
                lastCall = lastCallInformation.get("timeLastCall", None)
                log.info(f"manageLastCallJson : lastCall : {lastCall}")
                if lastCall is not None:
                    lastCall = datetime.datetime.strptime(
                        lastCall, "%Y-%m-%d %H:%M:%S.%f"
                    )
                    self.updateTimeLastCall(lastCall)
                lastUpdate = lastCallInformation.get("lastUpdate", None)
                log.info(f"manageLastCallJson : lastUpdate : {lastUpdate}")
                if lastUpdate is not None:
                    lastUpdate = datetime.datetime.strptime(
                        lastUpdate, "%Y-%m-%d %H:%M:%S.%f"
                    )
                    self.updateLastUpdate(lastCall)
                statutLastCall = lastCallInformation.get("statutLastCall", None)
                log.info(f"manageLastCallJson : statutLastCall : {statutLastCall}")
                if statutLastCall is not None:
                    self.updateStatusLastCall(statutLastCall)
                version = lastCallInformation.get("version", None)
                log.info(f"manageLastCallJson : previous version : {version}")
            except:
                # si le fichier est mal formaté
                pass

    def getPathArchive(self):
        return self._path

    def setlastCallJson(self):
        pass

        data = {
            "timeLastCall": str(self.getTimeLastCall()),
            "lastUpdate": str(self.getLastUpdate()),
            "statutLastCall": self.getStatusLastCall(),
            "version": self.getVersion(),
            # 'timeLastUpdate':self.getTimeLastCall()
        }
        # jsonData = json.dumps(data)
        self.setDataJsonValue("lastCall", data)

    def writeDataJson(self):
        import json

        directory = f"{self.getPathArchive()}/"
        for clef in self.getDataJsonKeys():
            try:
                data = {}
                nomfichier = directory + clef + ".json"
                data = self.getDataJsonValue(clef)
                # si la date est du timeout, alors on ecrit
                nePasEcrire = False
                if API.ENEDIS_RETURN in data:
                    enedis_return = data[API.ENEDIS_RETURN]
                    if API.ENEDIS_RETURN_ERROR in enedis_return:
                        nePasEcrire = enedis_return[API.ENEDIS_RETURN_ERROR] in (
                            "UNKERROR_TIMEOUT",
                            "UNAVAILABLE",
                        )
                log.info(f" >>>> ecriture : {nomfichier} / {data}")
                if not nePasEcrire:
                    with open(nomfichier, "w") as outfile:
                        json.dump(data, outfile)
            except:
                log.error(f" >>>> erreur ecriture : {nomfichier} / {data}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.error(sys.exc_info())

    def getData(self) -> bool:
        # ### A VOIR ###
        # # supprimer test ecrire sur ok present ou non !!! pas d'interet
        #   self.setDataJsonCopy() # pourquoi cela ? vu qu'on l'a mis juste
        #   avant ... pas besoin du default !!!!
        log.debug(f" {self._PDL_ID} >>>> getData, self._dataJson ? {self._dataJson}")
        forceCallJson = self._forceCallJson
        if not self.contract.isLoaded:
            log.debug(f"contract ? {self.contract.get_PDL_ID()}")
            try:
                if self.getCallPossible():
                    self.updateContract()
                if not self.contract.isLoaded:
                    self.contract.updateHCHP()
                log.debug(f"contract ?(end) {self.contract.get_PDL_ID()}")
            except Exception as inst:
                log.error(f"myEnedis err {inst}")
                log.error(traceback.format_exc())
                log.error("-" * 60)
                exc_type, exc_value, exc_traceback = sys.exc_info()
                log.warning(sys.exc_info())
                self.updateStatusLastCall(False)
                self.updateTimeLastCall()
                self.updateErrorLastCall(str(inst))
                log.error(f"LastMethodCall : {self.lastMethodCall}")

        if self.contract.isLoaded:
            self.update()
            self.setlastCallJson()
            log.info(f"UpdateRealise : {self.getUpdateRealise()}")
            if self.getUpdateRealise() and not forceCallJson:
                self.writeDataJson()

        else:
            # on a eut un probleme lors de l'appel
            pass
        return True

    @property
    def contract(self) -> myContrat:
        return self._contract

    @contract.setter
    def contract(self, c: myContrat):
        self._contract = c

    def isConsommation(self) -> bool:
        return True  # _consommation in self.contract["mode_PDL"]

    def isProduction(self) -> bool:
        return True  # _production in self.contract["mode_PDL"]

    def setDataJsonDefault(self, dataJsonDefault: dict[str, Any]):
        self._dataJsonDefault = dataJsonDefault

    def setDataJsonCopy(self):
        self._dataJson = self._dataJsonDefault.copy()

    def setDataJsonValue(self, key: str, value: Any):
        self._dataJson[key] = value

    def getDataJsonValue(self, key: str, default: Any = None) -> Any:
        return self._dataJson.get(key, default)

    def getDataJsonKeys(self):
        return self._dataJson.keys()

    def setDataRequestJson(self, key: str, myObjet):
        key = f"{key}_Req"
        self.setDataJsonValue(
            key,
            {
                "deb": myObjet.getDateDeb(),
                "fin": myObjet.getDateFin(),
                "callok": myObjet.getCallOk(),
            },
        )

    def getDataRequestJson(self, key: str) -> dict[str, Any]:
        key = f"{key}_Req"
        request = self.getDataJsonValue(key, {})
        return request

    def updateContract(self, indata=None):
        clefFunction = "updateContract"
        self.lastMethodCall = clefFunction
        log.debug(f"{self._PDL_ID} - updatecontract data : {indata}")
        if indata is None:
            indata = self.getDataJsonValue(clefFunction)
        log.debug(f"{self._PDL_ID} - updatecontract data : {indata}")
        data = self.contract.updateContract(indata)
        self.setDataJsonValue(clefFunction, data)

    def getYesterday(self):
        return self._yesterday

    def updateCurrentWeek(self, data=None, withControl=True):
        clefFunction = "updateCurrentWeek"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        cejour = today.strftime(_formatDateYmd)
        firstdateofweek = (
            today - datetime.timedelta(days=today.weekday() % 7)
        ).strftime(_formatDateYmd)

        deb = self.contract.minCompareDateContract(firstdateofweek)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._currentWeek.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._currentWeek)
        self.setNbCall(self._currentWeek.getNbCall())

    def updateLastWeek(self, data=None, withControl=True):
        clefFunction = "updateLastWeek"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        start_date = (today + datetime.timedelta(-today.weekday(), weeks=-1)).strftime(
            _formatDateYmd
        )
        end_date = (today + datetime.timedelta(-today.weekday())).strftime(
            _formatDateYmd
        )
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        data = self._lastWeek.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._lastWeek)
        self.setNbCall(self._lastWeek.getNbCall())

    def updateLast7Days(self, data=None, withControl=True):
        clefFunction = "updateLast7Days"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        data = self._last7Days.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._last7Days)
        self.setNbCall(self._last7Days.getNbCall())

    def updateDataYesterdayHCHP(self, data=None, _yesterdayDate=None, withControl=True):
        clefFunction = "updateDataYesterdayHCHP"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)

        today = datetime.date.today()
        hier = (today - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        # return self.getDataPeriodCLC(hier, cejour), hier
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._yesterdayHCHP.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._yesterdayHCHP)
        self.setNbCall(self._yesterdayHCHP.getNbCall())

    def updateLast7DaysDetails(self, data=None, _yesterdayDate=None, withControl=True):
        clefFunction = "updateLast7DaysDetails"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        data = self._last7DaysDetails.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._last7DaysDetails)
        self.setNbCall(self._last7DaysDetails.getNbCall())

    def updateCurrentMonth(self, data=None, withControl=True):
        clefFunction = "updateCurrentMonth"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        debCurrentMonth = today.replace(day=1).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        # if (debCurrentMonth != cejour):
        #    return self.getDataPeriod(debCurrentMonth, cejour)
        # else:
        #    return 0, False
        deb = self.contract.minCompareDateContract(debCurrentMonth)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._currentMonth.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._currentMonth)
        self.setNbCall(self._currentMonth.getNbCall())

    def updateLastMonth(self, data=None, withControl=True):
        clefFunction = "updateLastMonth"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)

        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonth.replace(day=1).strftime(_formatDateYmd)
        debCurrentMonth = first.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousMonth)
        fin = self.contract.maxCompareDateContract(debCurrentMonth)
        data = self._lastMonth.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._lastMonth)
        self.setNbCall(self._lastMonth.getNbCall())

    def updateLastMonthLastYear(self, data=None, withControl=True):
        clefFunction = "updateLastMonthLastYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        first = today.replace(day=1, year=today.year - 1)
        lastMonthLastYear = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonthLastYear.replace(day=1).strftime(_formatDateYmd)
        debCurrentMonth = first.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousMonth)
        fin = self.contract.maxCompareDateContract(debCurrentMonth)
        data = self._lastMonthLastYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._lastMonthLastYear)
        self.setNbCall(self._lastMonthLastYear.getNbCall())

    def updateCurrentYear(self, data=None, withControl=True):
        clefFunction = "updateCurrentYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        debCurrentMonth = today.replace(month=1, day=1).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debCurrentMonth)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._currentYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._currentYear)
        self.setNbCall(self._currentYear.getNbCall())

    def updateLastYear(self, data=None, withControl=True):
        clefFunction = "updateLastYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        first = today.replace(day=1, month=1)
        lastYear = first - datetime.timedelta(days=1)
        debPreviousYear = lastYear.replace(month=1, day=1).strftime(_formatDateYmd)
        debCurrentYear = today.replace(month=1, day=1).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousYear)
        fin = self.contract.maxCompareDateContract(debCurrentYear)
        data = self._lastYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._lastYear)
        self.setNbCall(self._lastYear.getNbCall())

    def updateYesterdayLastYear(self, data=None, withControl=True):
        clefFunction = "updateYesterdayLastYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        todayLastYear = today.replace(year=today.year - 1)
        hier = (todayLastYear - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = todayLastYear.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._yesterdayLastYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._yesterdayLastYear)
        self.setNbCall(self._yesterdayLastYear.getNbCall())

    def updateCurrentWeekLastYear(self, data=None, withControl=True) -> None:
        clefFunction = "updateCurrentWeekLastYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)

        today = datetime.date.today()
        numWeek = today.isocalendar()[1]  # numero de la semaine
        previousYear = today.year - 1
        d = f"{previousYear}-W{numWeek}"
        rfirstdateofweek = datetime.datetime.strptime(d + "-1", "%G-W%V-%u")
        # on recule d'un jour, car on a pas les données du jours,
        #   vs on a celle de l'an passé
        r = rfirstdateofweek + datetime.timedelta(
            days=today.weekday()
        )  # car on a pas les données du jour...
        # cejour = r.strftime(_formatDateYmd)
        r = rfirstdateofweek + datetime.timedelta(
            days=today.weekday()
        )  # car on a pas les données du jour...
        cejourmoins1 = r.strftime(_formatDateYmd)

        firstdateofweek = rfirstdateofweek.strftime(_formatDateYmd)

        deb = self.contract.minCompareDateContract(firstdateofweek)
        fin = self.contract.maxCompareDateContract(cejourmoins1)
        data = self._currentWeekLastYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._currentWeekLastYear)
        self.setNbCall(self._currentWeekLastYear.getNbCall())

    def updateCurrentMonthLastYear(self, data=None, withControl=True):
        clefFunction = "updateCurrentMonthLastYear"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)

        today = datetime.date.today()

        debCurrentMonthPreviousYear = today.replace(
            day=1, year=today.year - 1
        ).strftime(_formatDateYmd)
        cejourPreviousYear = today.replace(year=today.year - 1).strftime(_formatDateYmd)

        deb = self.contract.minCompareDateContract(debCurrentMonthPreviousYear)
        fin = self.contract.maxCompareDateContract(cejourPreviousYear)

        data = self._currentMonthLastYear.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._currentMonthLastYear)
        self.setNbCall(self._currentMonthLastYear.getNbCall())

    def updateYesterday(self, data=None, withControl=True):
        clefFunction = "updateYesterday"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        today = datetime.date.today()
        hier = (today - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        # print("data :", data)
        data = self._yesterday.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._yesterday)
        self.setNbCall(self._yesterday.getNbCall())

    def updateYesterdayProduction(self, data=None, withControl=True):
        clefFunction = "updateYesterdayProduction"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        data = self._productionYesterday.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._productionYesterday)
        self.setNbCall(self._productionYesterday.getNbCall())

    def updateEcoWatt(self, data=None, withControl=True):
        clefFunction = "updateEcoWatt"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        demain = (datetime.date.today() + datetime.timedelta(1)).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(demain)
        data = self._ecoWatt.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._ecoWatt)
        self.setNbCall(self._ecoWatt.getNbCall())

    def updateTempo(self, data=None, withControl=True):
        clefFunction = "updateTempo"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        demain = (datetime.date.today() + datetime.timedelta(1)).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(demain)
        data = self._tempo.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._tempo)
        self.setNbCall(self._tempo.getNbCall())

    def updateYesterdayConsumptionMaxPower(self, data=None, withControl=True):
        clefFunction = "updateYesterdayConsumptionMaxPower"
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = (datetime.date.today()).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        # val1, val2 = self.getDataPeriodConsumptionMaxPower(hier, cejour)
        data = self._yesterdayConsumptionMaxPower.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, self._yesterdayConsumptionMaxPower)
        self.setNbCall(self._yesterdayConsumptionMaxPower.getNbCall())

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

    # def CallgetCurrentMonthDetails(self):
    #    today = datetime.date.today()
    #    debCurrentMonth = today.replace(day=1).strftime(_formatDateYmd)
    #    cejour = today.strftime(_formatDateYmd)
    #    if debCurrentMonth != cejour:
    #        return self.getDataPeriodCLC(debCurrentMonth, cejour)
    #    else:
    #        return 0

    def getLastYear(self):
        return self._lastYear

    def getCurrentYear(self):
        return self._currentYear

    def getEcoWatt(self):
        return self._ecoWatt

    def getTempo(self):
        return self._tempo

    def getLastUpdate(self):
        return self._lastUpdate

    def updateLastUpdate(self, t="_unset"):
        if t == "_unset":
            t = datetime.datetime.now()
        self._lastUpdate = t

    def getTimeLastCall(self):
        return self._timeLastUpdate

    def updateTimeLastCall(self, t=None):
        # si on est dans le cas ou l'appel vient d'un forcage .. alors pas d'update
        if not self._forceCallJson:
            if t is None:
                t = datetime.datetime.now()
                self._timeLastUpdate = t
            else:
                self._timeLastUpdate = t
        else:
            if t is not None:
                self._timeLastUpdate = t

    def getStatusLastCall(self):
        return self._statusLastCall

    def getNbCall(self):
        return self._nbCall

    def setNbCall(self, nbCall):
        self._nbCall += nbCall

    def updateStatusLastCall(self, status):
        if (
            not self._forceCallJson
        ):  # pour eviter d'ecraser le statut quand on recupere la date depuis le json
            self._statusLastCall = status

    def getErrorLastCall(self):
        return self._errorLastCall

    def getCardErrorLastCall(self):
        lastAnswer = self._myCalli.getLastAnswer()
        if lastAnswer is None:
            return ""
        if API.ALERT_USER not in lastAnswer:
            return self.getErrorLastCall()
        if not lastAnswer[API.ALERT_USER]:
            return ""
        if (
            API.DESCRIPTION in lastAnswer
            and API.TAG in lastAnswer
            and API.ERROR_CODE in lastAnswer
        ):
            # si erreur autre que mauvais sens de lecture...
            if lastAnswer[API.ERROR_CODE] == "ADAM-ERR0069":
                return ""
            else:
                return "{} ({}-{})".format(
                    lastAnswer[API.DESCRIPTION],
                    lastAnswer[API.ERROR_CODE],
                    lastAnswer[API.TAG],
                )
        else:
            return self.getErrorLastCall()

    @property
    def lastMethodCall(self):
        return self._lastMethodCall

    @lastMethodCall.setter
    def lastMethodCall(self, methodName):
        self._lastMethodCall = methodName
        if self.lastMethodCallError == self._lastMethodCall:
            self.lastMethodCallError = ""
            self.updateStatusLastCall(
                True
            )  # pour la prochaine reprenne normalement car tout est conforme

    @property
    def lastMethodCallError(self):
        return self._lastMethodCallError

    @lastMethodCallError.setter
    def lastMethodCallError(self, methodName):
        self._lastMethodCallError = methodName

    def updateErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def setErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def getDelayError(self):
        return self._delay

    def getDelayIsGoodAfterError(self, currentDateTime):
        timeLastCall = self.getTimeLastCall()
        if timeLastCall is not None:
            minDelay = self.getDelayError()
            ecartOk = (
                currentDateTime.timestamp() - timeLastCall.timestamp()
            ) > minDelay
            log.info(
                "DelayIsGoodAfterError: Last:'%s' vs. Now:'%s' Δ%s %s",
                timeLastCall,
                currentDateTime,
                minDelay,
                ecartOk,
            )
        else:
            ecartOk = True
            log.info("DelayIsGoodAfterError: TimeLastCall is None, True")
        # test
        # ecartOk = True
        return ecartOk

    def getHoraireMin(self):
        return self._horaireMin.hour * 100 + self._horaireMin.minute

    def getHorairePossible(self):
        # hier 23h
        hourNow = datetime.datetime.now().hour * 100 + datetime.datetime.now().minute
        hourMin = self.getHoraireMin()
        horairePossible = (hourNow >= hourMin) and (hourNow < 2330)
        # for test
        # horairePossible = ( hourNow >= 11 ) and ( hourNow < 23 )
        log.info(f"HorairePossible: {hourMin}<={hourNow}<2330 => {horairePossible}")
        return horairePossible

    def getLastCallHier(self):
        """Return true if the last call was for yesterday"""
        if self.getTimeLastCall() is not None:
            hier = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(
                hour=23, minute=40
            )
            lastCall = self.getTimeLastCall()
            lastCallHier = lastCall.timestamp() < hier.timestamp()
        else:
            lastCallHier = False
        return lastCallHier

    def getGitVersion(self):
        # if self._gitVersion is None:
        #     await self.hass.async_add_executor_job(self.updateGitVersion())
        return self._gitVersion

    def updateGitVersion(self):
        # gitInfo = gitinformation.gitinformation(const.GITHUB_PRJ)
        # gitInfo.getInformation()
        # self._gitVersion = gitInfo.getVersion()
        self._gitVersion = ""

    def getCallPossible(self, trace=False):
        currentDateTime = datetime.datetime.now()

        callpossible = self.getHorairePossible() and (
            self.getLastCallHier()
            or (self.getTimeLastCall() is None)
            or (
                self.getStatusLastCall() is False
                and self.getDelayIsGoodAfterError(currentDateTime)
            )
        )

        # si on doit prendre les informations des fichiers de sauvegarde
        if self._forceCallJson:
            callpossible = True

        level = logging.ERROR if trace else logging.INFO
        log.log(
            level,
            "myEnedis ...new update self.getHorairePossible() : %s ??",
            self.getHorairePossible(),
        )
        log.log(
            level,
            "myEnedis ...new update self.getLastCallHier() : %s ??",
            self.getLastCallHier(),
        )
        log.log(
            level,
            "myEnedis ...new update self.getTimeLastCall() : %s ??",
            self.getTimeLastCall(),
        )
        log.log(
            level,
            "myEnedis ...new update self.getStatusLastCall() : %s??",
            self.getStatusLastCall(),
        )
        log.log(
            level,
            "myEnedis ...new update self.getDelayIsGoodAfterError() : %s??",
            self.getDelayIsGoodAfterError(currentDateTime),
        )
        log.log(level, f"myEnedis ..._forceCallJson : {self._forceCallJson}??")
        log.log(level, f"myEnedis ...<< call Possible >> : {callpossible}??")
        return callpossible

    def callConsommation(self):
        if self.isConsommation():
            self._niemeAppel += 1
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateYesterday"
            ):
                self.updateYesterday()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateCurrentWeek"
            ):
                self.updateCurrentWeek()
            if self.getStatusLastCall() or self.lastMethodCallError == "updateLastWeek":
                self.updateLastWeek()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateLast7Days"
            ):
                self.updateLast7Days()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateDataYesterdayHCHP"
            ):
                self.updateDataYesterdayHCHP()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateLast7DaysDetails"
            ):
                self.updateLast7DaysDetails()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateCurrentMonth"
            ):
                self.updateCurrentMonth()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateLastMonth"
            ):
                self.updateLastMonth()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateLastMonthLastYear"
            ):
                self.updateLastMonthLastYear()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateCurrentYear"
            ):
                self.updateCurrentYear()
            if self.getStatusLastCall() or self.lastMethodCallError == "updateLastYear":
                self.updateLastYear()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateYesterdayLastYear"
            ):
                self.updateYesterdayLastYear()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateCurrentWeekLastYear"
            ):
                self.updateCurrentWeekLastYear()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateYesterdayConsumptionMaxPower"
            ):
                self.updateYesterdayConsumptionMaxPower()
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateCurrentMonthLastYear"
            ):
                self.updateCurrentMonthLastYear()

            if not self._forceCallJson:
                self.updateTimeLastCall()
            self.updateStatusLastCall(True)
            log.info("mise à jour effectuee consommation")

    def callProduction(self):
        if self.isProduction():
            if (
                self.getStatusLastCall()
                or self.lastMethodCallError == "updateYesterdayProduction"
            ):
                self.updateYesterdayProduction()
            self.updateTimeLastCall()
            self.updateStatusLastCall(True)
            log.info("mise à jour effectuee production")

    def callEcoWatt(self):
        if ((self.getStatusLastCall() or self.lastMethodCallError == "updateEcoWatt")
                and (self.getServiceEnedis() == _ENEDIS_MyElectricData)):
            self.updateEcoWatt()
        self.updateTimeLastCall()
        self.updateStatusLastCall(True)
        log.info("mise à jour effectuee EcoWatt")

    def callTempo(self):
        if ((self.getStatusLastCall() or self.lastMethodCallError == "updateTempo")
                and (self.getServiceEnedis() == _ENEDIS_MyElectricData)):
            self.updateTempo()
        self.updateTimeLastCall()
        self.updateStatusLastCall(True)
        log.info("mise à jour effectuee Tempo")

    def update(self):  # noqa C901
        log.info(f"myEnedis ...new update ?? {self._PDL_ID}")
        if self.contract.isLoaded:
            if self.getCallPossible():
                try:
                    log.info(
                        "myEnedis(%s) ...%s update lancé,"
                        " status precedent : %s, lastMethodCall :%s,"
                        " forcejson :%s",
                        self.getVersion(),
                        self.contract.get_PDL_ID(),
                        self.getStatusLastCall(),
                        self.lastMethodCallError,
                        self._forceCallJson,
                    )
                    # self.getCallPossible()
                    self._nbCall = 0
                    self.updateGitVersion()
                    self.updateErrorLastCall("")
                    self.lastMethodCall = ""
                    self.setUpdateRealise(True)
                    if (
                        not self._forceCallJson
                    ):  # si pas un forcage alors on reset le last call...
                        self.updateStatusLastCall(True)
                    try:
                        self.callConsommation()
                        self.callProduction()
                        self.callEcoWatt()
                        self.callTempo()
                        if self._forceCallJson:
                            self._forceCallJson = False
                            self.setDataJsonDefault({})

                        log.info(
                            "myEnedis(%s) ... %s update termine,"
                            " status courant : %s, lastCall :%s, nbCall :%s",
                            self.getVersion(),
                            self.contract.get_PDL_ID(),
                            self.getStatusLastCall(),
                            self.lastMethodCallError,
                            self.getNbCall(),
                        )
                    except Exception as inst:
                        # pour eviter de boucler le call en permanence
                        if self._forceCallJson:
                            self._forceCallJson = False
                            self.setDataJsonDefault({})
                        if inst.args[:2] == (
                            "call",
                            "error",
                        ):  # gestion que c'est pas une erreur de contrat trop recent ?
                            log.error(
                                "%s - Erreur call ERROR %s",
                                self.contract.get_PDL_ID(),
                                inst,
                            )
                            # Erreur lors du call...
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self.updateErrorLastCall(
                                "{} - {}".format(
                                    messages.getMessage(inst.args[2]),
                                    self._myCalli.getLastAnswer(),
                                )
                            )
                            log.error(
                                "%s - last call : %s",
                                self.contract.get_PDL_ID(),
                                self.lastMethodCall,
                            )
                            log.error(
                                "myEnedis ...%s update termine,"
                                " on retentera plus tard(A1)",
                                self.contract.get_PDL_ID(),
                            )
                        elif inst.args[:2] == (
                            "call",
                            "error_user_alert",
                        ):  # gestion que c'est pas une erreur de contrat trop recent ?
                            log.error(
                                "%s - Erreur call ERROR %s",
                                self.contract.get_PDL_ID(),
                                inst,
                            )
                            # Erreur lors du call...
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self._myCalli.setLastAnswer("Enedis")
                            self.updateErrorLastCall(
                                "%s - %s"
                                % (
                                    messages.getMessage(inst.args[2]),
                                    self._myCalli.getLastAnswer(),
                                )
                            )
                            log.error(
                                "%s - last call : %s",
                                self.contract.get_PDL_ID(),
                                self.lastMethodCall,
                            )
                            log.error(
                                "myEnedis ...%s update termine,"
                                " on retentera plus tard(A2)",
                                self.contract.get_PDL_ID(),
                            )
                        else:
                            self.updateTimeLastCall()
                            self.updateStatusLastCall(False)
                            self.updateErrorLastCall(str(self._myCalli.getLastAnswer()))
                            log.error(
                                "%s - last call : %s",
                                self.contract.get_PDL_ID(),
                                self.lastMethodCall,
                            )
                            log.error(
                                "myEnedis ...%s update termine,"
                                " on retentera plus tard(B)",
                                self.contract.get_PDL_ID(),
                            )
                            raise Exception(inst)

                except Exception as inst:
                    if inst.args == ("call", None):
                        log.error("*" * 60)
                        log.error(f"{self.contract.get_PDL_ID()} - Erreur call")
                        self.updateTimeLastCall()
                        self.updateStatusLastCall(False)
                        message = "{} - {}".format(
                            messages.getMessage(inst.args[2]),
                            self._myCalli.getLastAnswer(),
                        )
                        self.updateErrorLastCall(message)
                        log.error(
                            "%s - %s",
                            self.contract.get_PDL_ID(),
                            self.lastMethodCall,
                        )
                    else:
                        log.error("-" * 60)
                        log.error("Erreur inconnue call ERROR %s", inst)
                        log.error("Erreur last answer %s", inst)
                        log.error(f"Erreur last call {self.lastMethodCall}")
                        log.error(f"Erreur last answer {self._myCalli.getLastAnswer()}")
                        log.error(traceback.format_exc())
                        log.error("-" * 60)
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        log.warning(sys.exc_info())
                        self.updateStatusLastCall(False)
                        self.updateTimeLastCall()
                        self.updateErrorLastCall(str(inst))
                        log.error(f"LastMethodCall : {self.lastMethodCall}")
            else:
                self.setUpdateRealise(False)
                # log.info("%s pas d'update trop tot !!!", self.contract.get_PDL_ID())
        else:
            self.setUpdateRealise(False)
            log.info(
                "%s update impossible contrat non trouve!!!", self.contract.get_PDL_ID()
            )
        self.updateLastUpdate()
        return True
