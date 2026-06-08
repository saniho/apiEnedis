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
from . import client_call_orchestrator as call_orch
from . import client_getters as getters
from .client_file_store import FileStore
from .exceptions import EnedisApiError, EnedisAuthError, EnedisDataError
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
        self._file_store = FileStore(self._path, self._PDL_ID)

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
        return getters.get_version(self)

    def setUpdateRealise(self, value: bool):
        self._updateRealise = value

    def getUpdateRealise(self) -> bool:
        return getters.get_update_realise(self)

    def setPathArchive(self, path: str):
        self._path = path
        self._file_store = FileStore(self._path, self._PDL_ID)

    def getServiceEnedis(self):
        return getters.get_service_enedis(self)

    def readDataJson(self):
        return self._file_store.read_all()

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
            except Exception:
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
        data = {}
        for clef in self.getDataJsonKeys():
            data[clef] = self.getDataJsonValue(clef)
        self._file_store.write_all(data)

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
        return getters.get_yesterday(self)

    def _run_update(self, clefFunction, data_obj, deb, fin, data=None, withControl=True):
        self.lastMethodCall = clefFunction
        requestJson = self.getDataRequestJson(clefFunction)
        if data is None:
            data = self.getDataJsonValue(clefFunction)
        data = data_obj.updateData(
            clefFunction,
            self.getHorairePossible(),
            data,
            deb,
            fin,
            withControl=withControl,
            dataControl=requestJson,
        )
        self.setDataJsonValue(clefFunction, data)
        self.setDataRequestJson(clefFunction, data_obj)
        self.setNbCall(data_obj.getNbCall())

    def updateCurrentWeek(self, data=None, withControl=True):
        today = datetime.date.today()
        cejour = today.strftime(_formatDateYmd)
        firstdateofweek = (
            today - datetime.timedelta(days=today.weekday() % 7)
        ).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(firstdateofweek)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateCurrentWeek", self._currentWeek, deb, fin, data, withControl)

    def updateLastWeek(self, data=None, withControl=True):
        today = datetime.date.today()
        start_date = (today + datetime.timedelta(-today.weekday(), weeks=-1)).strftime(
            _formatDateYmd
        )
        end_date = (today + datetime.timedelta(-today.weekday())).strftime(
            _formatDateYmd
        )
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        self._run_update("updateLastWeek", self._lastWeek, deb, fin, data, withControl)

    def updateLast7Days(self, data=None, withControl=True):
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        self._run_update("updateLast7Days", self._last7Days, deb, fin, data, withControl)

    def updateDataYesterdayHCHP(self, data=None, _yesterdayDate=None, withControl=True):
        today = datetime.date.today()
        hier = (today - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateDataYesterdayHCHP", self._yesterdayHCHP, deb, fin, data, withControl)

    def updateLast7DaysDetails(self, data=None, _yesterdayDate=None, withControl=True):
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(7)).strftime(_formatDateYmd)
        end_date = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(start_date)
        fin = self.contract.maxCompareDateContract(end_date)
        self._run_update("updateLast7DaysDetails", self._last7DaysDetails, deb, fin, data, withControl)

    def updateCurrentMonth(self, data=None, withControl=True):
        today = datetime.date.today()
        debCurrentMonth = today.replace(day=1).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debCurrentMonth)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateCurrentMonth", self._currentMonth, deb, fin, data, withControl)

    def updateLastMonth(self, data=None, withControl=True):
        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonth.replace(day=1).strftime(_formatDateYmd)
        debCurrentMonth = first.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousMonth)
        fin = self.contract.maxCompareDateContract(debCurrentMonth)
        self._run_update("updateLastMonth", self._lastMonth, deb, fin, data, withControl)

    def updateLastMonthLastYear(self, data=None, withControl=True):
        today = datetime.date.today()
        first = today.replace(day=1, year=today.year - 1)
        lastMonthLastYear = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonthLastYear.replace(day=1).strftime(_formatDateYmd)
        debCurrentMonth = first.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousMonth)
        fin = self.contract.maxCompareDateContract(debCurrentMonth)
        self._run_update("updateLastMonthLastYear", self._lastMonthLastYear, deb, fin, data, withControl)

    def updateCurrentYear(self, data=None, withControl=True):
        today = datetime.date.today()
        debCurrentYear = today.replace(month=1, day=1).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debCurrentYear)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateCurrentYear", self._currentYear, deb, fin, data, withControl)

    def updateLastYear(self, data=None, withControl=True):
        today = datetime.date.today()
        first = today.replace(day=1, month=1)
        lastYear = first - datetime.timedelta(days=1)
        debPreviousYear = lastYear.replace(month=1, day=1).strftime(_formatDateYmd)
        debCurrentYear = today.replace(month=1, day=1).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(debPreviousYear)
        fin = self.contract.maxCompareDateContract(debCurrentYear)
        self._run_update("updateLastYear", self._lastYear, deb, fin, data, withControl)

    def updateYesterdayLastYear(self, data=None, withControl=True):
        today = datetime.date.today()
        todayLastYear = today.replace(year=today.year - 1)
        hier = (todayLastYear - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = todayLastYear.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateYesterdayLastYear", self._yesterdayLastYear, deb, fin, data, withControl)

    def updateCurrentWeekLastYear(self, data=None, withControl=True) -> None:
        today = datetime.date.today()
        numWeek = today.isocalendar()[1]
        previousYear = today.year - 1
        d = f"{previousYear}-W{numWeek}"
        rfirstdateofweek = datetime.datetime.strptime(d + "-1", "%G-W%V-%u")
        r = rfirstdateofweek + datetime.timedelta(days=today.weekday())
        cejourmoins1 = r.strftime(_formatDateYmd)
        firstdateofweek = rfirstdateofweek.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(firstdateofweek)
        fin = self.contract.maxCompareDateContract(cejourmoins1)
        self._run_update("updateCurrentWeekLastYear", self._currentWeekLastYear, deb, fin, data, withControl)

    def updateCurrentMonthLastYear(self, data=None, withControl=True):
        today = datetime.date.today()
        deb = self.contract.minCompareDateContract(
            today.replace(day=1, year=today.year - 1).strftime(_formatDateYmd)
        )
        fin = self.contract.maxCompareDateContract(
            today.replace(year=today.year - 1).strftime(_formatDateYmd)
        )
        self._run_update("updateCurrentMonthLastYear", self._currentMonthLastYear, deb, fin, data, withControl)

    def updateYesterday(self, data=None, withControl=True):
        today = datetime.date.today()
        hier = (today - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = today.strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateYesterday", self._yesterday, deb, fin, data, withControl)

    def updateYesterdayProduction(self, data=None, withControl=True):
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = datetime.date.today().strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateYesterdayProduction", self._productionYesterday, deb, fin, data, withControl)

    def updateEcoWatt(self, data=None, withControl=True):
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        demain = (datetime.date.today() + datetime.timedelta(1)).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(demain)
        self._run_update("updateEcoWatt", self._ecoWatt, deb, fin, data, withControl)

    def updateTempo(self, data=None, withControl=True):
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        demain = (datetime.date.today() + datetime.timedelta(1)).strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(demain)
        self._run_update("updateTempo", self._tempo, deb, fin, data, withControl)

    def updateYesterdayConsumptionMaxPower(self, data=None, withControl=True):
        hier = (datetime.date.today() - datetime.timedelta(1)).strftime(_formatDateYmd)
        cejour = datetime.date.today().strftime(_formatDateYmd)
        deb = self.contract.minCompareDateContract(hier)
        fin = self.contract.maxCompareDateContract(cejour)
        self._run_update("updateYesterdayConsumptionMaxPower", self._yesterdayConsumptionMaxPower, deb, fin, data, withControl)

    def getYesterdayLastYear(self):
        return getters.get_yesterday_last_year(self)

    def getYesterdayConsumptionMaxPower(self):
        return getters.get_yesterday_consumption_max_power(self)

    def getProductionYesterday(self):
        return getters.get_production_yesterday(self)

    def getYesterdayHCHP(self):
        return getters.get_yesterday_hchp(self)

    def getHCCost(self, val):
        return getters.get_hc_cost(self, val)

    def getHPCost(self, val):
        return getters.get_hp_cost(self, val)

    def getLastMonth(self):
        return getters.get_last_month(self)

    def getLastMonthLastYear(self):
        return getters.get_last_month_last_year(self)

    def getLastWeek(self):
        return getters.get_last_week(self)

    def getLast7Days(self):
        return getters.get_last_7_days(self)

    def getLast7DaysDetails(self):
        return getters.get_last_7_days_details(self)

    def getCurrentWeek(self):
        return getters.get_current_week(self)

    def getCurrentWeekLastYear(self):
        return getters.get_current_week_last_year(self)

    def getCurrentMonthLastYear(self):
        return getters.get_current_month_last_year(self)

    def getCurrentMonth(self):
        return getters.get_current_month(self)

    def getLastYear(self):
        return getters.get_last_year(self)

    def getCurrentYear(self):
        return getters.get_current_year(self)

    def getEcoWatt(self):
        return getters.get_ecowatt(self)

    def getTempo(self):
        return getters.get_tempo(self)

    def getLastUpdate(self):
        return getters.get_last_update(self)

    def getTimeLastCall(self):
        return getters.get_time_last_call(self)

    def getStatusLastCall(self):
        return getters.get_status_last_call(self)

    def getNbCall(self):
        return getters.get_nb_call(self)

    def getErrorLastCall(self):
        return getters.get_error_last_call(self)

    def getDelayError(self):
        return getters.get_delay_error(self)

    def getGitVersion(self):
        return getters.get_git_version(self)

    def updateLastUpdate(self, t="_unset"):
        if t == "_unset":
            t = datetime.datetime.now()
        self._lastUpdate = t

    def updateTimeLastCall(self, t=None):
        if not self._forceCallJson:
            if t is None:
                t = datetime.datetime.now()
                self._timeLastUpdate = t
            else:
                self._timeLastUpdate = t
        else:
            if t is not None:
                self._timeLastUpdate = t

    def setNbCall(self, nbCall):
        self._nbCall += nbCall

    def updateStatusLastCall(self, status):
        if not self._forceCallJson:
            self._statusLastCall = status

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
            if lastAnswer[API.ERROR_CODE] == "ADAM-ERR0069":
                return ""
            return "{} ({}-{})".format(
                lastAnswer[API.DESCRIPTION],
                lastAnswer[API.ERROR_CODE],
                lastAnswer[API.TAG],
            )
        return self.getErrorLastCall()

    @property
    def lastMethodCall(self):
        return self._lastMethodCall

    @lastMethodCall.setter
    def lastMethodCall(self, methodName):
        self._lastMethodCall = methodName
        if self.lastMethodCallError == self._lastMethodCall:
            self.lastMethodCallError = ""
            self.updateStatusLastCall(True)

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
        return ecartOk

    def getHoraireMin(self):
        return self._horaireMin.hour * 100 + self._horaireMin.minute

    def getHorairePossible(self):
        hourNow = datetime.datetime.now().hour * 100 + datetime.datetime.now().minute
        hourMin = self.getHoraireMin()
        horairePossible = (hourNow >= hourMin) and (hourNow < 2330)
        log.info(f"HorairePossible: {hourMin}<={hourNow}<2330 => {horairePossible}")
        return horairePossible

    def getLastCallHier(self):
        if self.getTimeLastCall() is not None:
            hier = (datetime.datetime.now() - datetime.timedelta(days=1)).replace(
                hour=23, minute=40
            )
            lastCall = self.getTimeLastCall()
            lastCallHier = lastCall.timestamp() < hier.timestamp()
        else:
            lastCallHier = False
        return lastCallHier

    def updateGitVersion(self):
        self._gitVersion = ""

    def getCallPossible(self, trace=False):
        return call_orch.get_call_possible(self, trace)

    def callConsommation(self):
        call_orch.call_consommation(self)

    def callProduction(self):
        call_orch.call_production(self)

    def callEcoWatt(self):
        call_orch.call_ecowatt(self)

    def callTempo(self):
        call_orch.call_tempo(self)

    def update(self):
        return call_orch.do_update(self)
