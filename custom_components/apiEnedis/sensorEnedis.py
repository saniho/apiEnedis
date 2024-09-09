from __future__ import annotations

import datetime
import sys
import traceback
from collections import defaultdict

try:
    from .const import _consommation, _production, \
        _formatDateYmdHMS

except ImportError:
    from const import _consommation, _production, \
        _formatDateYmdHMS  # type: ignore[no-redef]

__nameManageSensorState__ = "manageSensorState"
import logging


class manageSensorState:
    def __init__(self):
        self._init = False

    def getInit(self):
        return self._init

    def setInit(self, val):
        self._init = val

    def init(self, _myDataEnedis, _LOGGER=None, version=None):
        # enedis à initialiser ici!!!
        self._myDataEnedis = _myDataEnedis
        if _LOGGER is None:
            _LOGGER = logging.getLogger(__nameManageSensorState__)
        self._LOGGER = _LOGGER
        self.version = version
        self.setInit(True)

    def get_PDL_ID(self):
        return self._myDataEnedis.contract.get_PDL_ID()

    def getStatusYesterdayCost(self):
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        dataAvailable = False
        yesterdayDate = None
        if self._myDataEnedis.contract is not None:
            if (
                self._myDataEnedis.getYesterdayHCHP().getHC()
                + self._myDataEnedis.getYesterdayHCHP().getHP()
            ) != 0:  # on a eut des données
                status_counts["yesterday_HC_cost"] = "{:.3f}".format(
                    0.001
                    * self._myDataEnedis.getHCCost(
                        self._myDataEnedis.getYesterdayHCHP().getHC()
                    )
                )
                status_counts["yesterday_HP_cost"] = "{:.3f}".format(
                    0.001
                    * self._myDataEnedis.getHPCost(
                        self._myDataEnedis.getYesterdayHCHP().getHP()
                    )
                )
                daily_cost = "{:.2f}".format(
                    0.001
                    * self._myDataEnedis.getHCCost(
                        self._myDataEnedis.getYesterdayHCHP().getHC()
                    )
                    + 0.001
                    * self._myDataEnedis.getHPCost(
                        self._myDataEnedis.getYesterdayHCHP().getHP()
                    )
                )
                yesterdayDate = self._myDataEnedis.getYesterday().getDateDeb()
                status_counts["daily_cost"] = daily_cost
                state = daily_cost
                dataAvailable = True
        return dataAvailable, yesterdayDate, status_counts, state

    def getStatusHistory(self, laDate, detail="ALL", typeSensor=_consommation):
        state: int | str = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        clefDate = laDate.strftime("%Y-%m-%d %H")
        status_counts["DateHeure"] = clefDate
        status_counts["detail"] = detail
        if self._myDataEnedis.contract is not None:
            if self._myDataEnedis.isConsommation():
                state = 0
                DateHeureDetail = {}
                if detail == "ALL":
                    DateHeureDetail = (
                        self._myDataEnedis.getLast7DaysDetails().getDateHeureDetail()
                    )
                if detail == "HP":
                    DateHeureDetail = (
                        self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHP()
                    )
                if detail == "HC":
                    DateHeureDetail = (
                        self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHC()
                    )
                if clefDate in DateHeureDetail.keys():
                    state = DateHeureDetail[clefDate] * 0.001
        return status_counts, state

    def getExistsRecentVersion(self, versionCurrent, versionGit):
        # import packaging.version
        #
        # # If only one of the versions exists, result is False
        # if (versionCurrent is None) or (versionGit is None) or (versionGit == ""):
        #     return False
        #
        # # self._LOGGER.error(
        # #    "-- ** versionGit : %s, versionGit : %s" %( versionCurrent, versionGit )
        # # )
        # # Get version representations
        # currVersionObj = packaging.version.parse(versionCurrent)
        # try:
        #     # version par encore disponible
        #     gitVersionObj = packaging.version.parse(versionGit)
        # except:
        #     return False
        # return currVersionObj < gitVersionObj
        return False

    def getStatusEnergy(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts: dict[str, int] = defaultdict(int)
        if self._myDataEnedis.getTimeLastCall() is not None:
            state = "{:.3f}".format(
                self._myDataEnedis.getCurrentYear().getValue() * 0.001
            )

        return status_counts, state

    def getStatusEcoWatt(self):
        # import random
        state = ""
        status_counts: dict[str, str] = defaultdict(str)

        status_counts["version"] = self.version

        status_counts["lastSensorCall"] = \
            datetime.datetime.now().strftime(format=_formatDateYmdHMS)

        today = datetime.datetime.today().replace(minute=0, second=0, microsecond=0)
        end = datetime.datetime.now() + datetime.timedelta(hours=12)
        end = end.replace(minute=0, second=0, microsecond=0)
        status_counts["forecast"] = {}
        for maDate in self._myDataEnedis.getEcoWatt().getValue().keys():
            if (maDate >= today) and (maDate < end):
                clef = maDate.strftime(format="%H h")
                valeur = self._myDataEnedis.getEcoWatt().getValue()[maDate]
                # valeur = random.randrange(3) + 1 # pour mettre des valeurs aléatoire
                status_counts["forecast"][clef] = valeur
        status_counts["begin"] = today
        status_counts["end"] = end
        # ajout last update du sensor a
        if self._myDataEnedis.getTimeLastCall() is not None:
            state = "{:.3f}".format(
                123456
            )
        return status_counts, state

    def getStatusTempo(self):
        # import random
        state = ""
        status_counts: dict[str, str] = defaultdict(str)

        status_counts["version"] = self.version

        status_counts["lastSensorCall"] = \
            datetime.datetime.now().strftime(format="%Y-%m-%d %H:%M:%S")

        today = datetime.datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0)
        end = datetime.datetime.now() + datetime.timedelta(days=3)
        end = end.replace(minute=0, second=0, microsecond=0)
        status_counts["forecast"] = {}
        for maDate in self._myDataEnedis.getTempo().getValue().keys():
            if (maDate >= today) and (maDate < end):
                clef = maDate.strftime(format="%Y-%m-%d")
                valeur = self._myDataEnedis.getTempo().getValue()[maDate]
                # valeur = random.randrange(3) + 1 # pour mettre des valeurs aléatoire
                status_counts["forecast"][clef] = valeur
                if maDate == today:
                    state = valeur
        status_counts["begin"] = today
        status_counts["end"] = end
        return status_counts, state

    def getStatusEnergyDetailHours(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts: dict[str, int] = defaultdict(int)
        # "last_reset": "2021-01-01T00:00:00",  # à corriger plus tard !!

        laDate = datetime.datetime.today() - datetime.timedelta(2)
        laDate = laDate.replace(minute=0, second=0, microsecond=0)
        lastReset = laDate
        if self._myDataEnedis.getTimeLastCall() is not None:
            # DateHeureDetail = {}
            DateHeureDetailHP = (
                self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHP()
            )
            DateHeureDetailHC = (
                self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHC()
            )
            clefDate = laDate.strftime("%Y-%m-%d %H")
            valeurHP, valeurHC = 0, 0
            if clefDate in DateHeureDetailHP.keys():
                valeurHP = DateHeureDetailHP[clefDate]
            if clefDate in DateHeureDetailHC.keys():
                valeurHC = DateHeureDetailHC[clefDate]

            total = valeurHP + valeurHC
            state = f"{0.001 * total:.3f}"
        # on recule d'une heure, car il faut indiquer le dernier "changement"
        lastResetIso = (lastReset - datetime.timedelta(hours=1)).isoformat()
        return lastResetIso, status_counts, state

    def getStatusEnergyDetailHoursCost(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts: dict[str, int] = defaultdict(int)
        # "last_reset": "2021-01-01T00:00:00",  # à corriger plus tard !!

        laDate = datetime.datetime.today() - datetime.timedelta(2)
        laDate = laDate.replace(minute=0, second=0, microsecond=0)
        lastReset = laDate
        if self._myDataEnedis.getTimeLastCall() is not None:
            # DateHeureDetail = {}
            DateHeureDetailHP = (
                self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHP()
            )
            DateHeureDetailHC = (
                self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHC()
            )
            clefDate = laDate.strftime("%Y-%m-%d %H")
            valeurHP, valeurHC = 0, 0
            if clefDate in DateHeureDetailHP.keys():
                valeurHP = DateHeureDetailHP[clefDate]
            if clefDate in DateHeureDetailHC.keys():
                valeurHC = DateHeureDetailHC[clefDate]

            # costHC = f"{0.001 * self._myDataEnedis.getHCCost(valeurHC):.3f}"
            # costHP = f"{0.001 * self._myDataEnedis.getHPCost(valeurHP):.3f}"
            cost = self._myDataEnedis.getHCCost(
                valeurHC
            ) + self._myDataEnedis.getHPCost(valeurHP)
            state = f"{0.001 * cost:.3f}"
        lastResetIso = lastReset.isoformat()
        return lastResetIso, status_counts, state

    def getStatus(self, typeSensor=_consommation):  # noqa C901
        # Raccourci pour self._myDataEnedis (lignes plus court)
        data = self._myDataEnedis

        state = "unavailable"
        status: dict[str, int | float | str | list] = defaultdict(int)
        status["version"] = self.version
        status["versionGit"] = data.getGitVersion()
        status["serviceEnedis"] = data.getServiceEnedis()
        status["versionUpdateAvailable"] = self.getExistsRecentVersion(
            self.version, data.getGitVersion()
        )

        if data.getTimeLastCall() is not None:
            self._LOGGER.info(
                "-- ** on va mettre à jour : %s", data.contract.get_PDL_ID()
            )
            status["nbCall"] = data.getNbCall()
            status["typeCompteur"] = typeSensor
            status["numPDL"] = data.contract.get_PDL_ID()
            status["horaireMinCall"] = data.getHoraireMin()
            status["activationDate"] = data.contract.getLastActivationDate()
            if data.isConsommation():
                status["lastUpdate"] = data.getLastUpdate()
                status["timeLastCall"] = data.getTimeLastCall()
                # à supprimer car doublon avec j_1
                status["yesterday"] = data.getYesterday().getValue()
                status["last_week"] = data.getLastWeek().getValue()

            if 1:  # data.getStatusLastCall():  # update avec statut ok
                try:
                    # typesensor ... fonction de  ?
                    if typeSensor == _consommation:  # data.isConsommation():
                        valeur: int | str

                        status["lastUpdate"] = data.getLastUpdate()
                        status["timeLastCall"] = data.getTimeLastCall()
                        # à supprimer car doublon avec j_1
                        status["yesterday"] = data.getYesterday().getValue()
                        status["yesterdayDate"] = data.getYesterday().getDateDeb()
                        status[
                            "yesterdayLastYear"
                        ] = data.getYesterdayLastYear().getValue()
                        status[
                            "yesterdayLastYearDate"
                        ] = data.getYesterday().getDateDeb()
                        status[
                            "yesterdayConsumptionMaxPower"
                        ] = data.getYesterdayConsumptionMaxPower().getValue()
                        status["last_week"] = data.getLastWeek().getValue()
                        last7daysHP = data.getLast7DaysDetails().getDaysHP()

                        # TODO: Verifier si les deux lignes suivants sont utiles!
                        listeClef: list[str] = list(last7daysHP.keys())
                        listeClef.reverse()

                        today = datetime.date.today()
                        listeClef = []
                        for i in range(7):
                            maDate = today - datetime.timedelta(i + 1)
                            listeClef.append(maDate.strftime("%Y-%m-%d"))
                        niemejour = 0
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeur = last7daysHP[clef]
                            status[f"day_{niemejour}_HP"] = valeur
                        last7daysHC = data.getLast7DaysDetails().getDaysHC()
                        niemejour = 0
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = last7daysHC[clef]
                            status[f"day_{niemejour}_HC"] = valeur
                        # gestion du cout par jour ....

                        niemejour = 0
                        cout = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (
                                clef in last7daysHC.keys()
                                and clef in last7daysHP.keys()
                            ):
                                valeur = 0.001 * data.getHCCost(
                                    last7daysHC[clef]
                                ) + 0.001 * data.getHPCost(last7daysHP[clef])
                                valeur = f"{valeur:.2f}"
                            cout.append(valeur)
                        status["dailyweek_cost"] = cout
                        niemejour = 0
                        coutHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = 0.001 * data.getHCCost(last7daysHC[clef])
                                valeur = f"{valeur:.2f}"
                            coutHC.append(valeur)
                        status["dailyweek_costHC"] = coutHC

                        niemejour = 0
                        dailyHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = f"{0.001 * last7daysHC[clef]:.3f}"
                            dailyHC.append(valeur)
                        status["dailyweek_HC"] = dailyHC

                        status["dailyweek"] = list(listeClef)  # listeClef -> days
                        niemejour = 0
                        coutHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeurFloat = 0.001 * data.getHPCost(last7daysHP[clef])
                                valeur = f"{valeurFloat:.2f}"
                            coutHP.append(valeur)
                        status["dailyweek_costHP"] = coutHP
                        # gestion du format : "{:.2f}".format(a)

                        niemejour = 0
                        dailyHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeurFloat = last7daysHP[clef]
                                valeur = f"{0.001 * valeurFloat:.3f}"
                            dailyHP.append(valeur)
                        status["dailyweek_HP"] = dailyHP

                        niemejour = 0
                        daily = []
                        for clef in listeClef:
                            niemejour += 1
                            somme: int | float | str = -1
                            if (
                                clef in last7daysHP.keys()
                                and clef in last7daysHC.keys()
                            ):
                                sommeFloat = last7daysHP[clef] + last7daysHC[clef]
                                somme = f"{0.001 * sommeFloat:.2f}"
                            status[f"day_{niemejour}"] = somme
                            daily.append(somme)
                        status["daily"] = daily

                        status["halfhourly"] = []

                        # Intermediate variables
                        prevDayHC = data.getYesterdayHCHP().getHC()
                        prevDayHCCost = data.getHCCost(prevDayHC) * 0.001
                        prevDayHP = data.getYesterdayHCHP().getHP()
                        prevDayHPCost = data.getHPCost(prevDayHP) * 0.001
                        prevDailyCost = prevDayHCCost + prevDayHPCost

                        status["offpeak_hours"] = f"{prevDayHC * 0.001:.3f}"
                        status["peak_hours"] = f"{prevDayHP * 0.001:.3f}"

                        # Get Yesterday's HP/(HP+HC) in %
                        prevDayHPHC = prevDayHC + prevDayHP
                        if prevDayHPHC != 0:  # Pas de division par 0
                            valeur = (prevDayHP * 100) / prevDayHPHC
                            status["peak_offpeak_percent"] = f"{valeur:.2f}"
                        else:
                            status["peak_offpeak_percent"] = 0

                        status["yesterday_HC_cost"] = f"{prevDayHCCost:.3f}"
                        status["yesterday_HP_cost"] = f"{prevDayHPCost:.3f}"
                        status["daily_cost"] = f"{prevDailyCost:.2f}"
                        status["yesterday_HC"] = f"{prevDayHC * 0.001:.3f}"
                        status["yesterday_HP"] = f"{prevDayHP * 0.001:.3f}"
                        status["yesterday_HCHP"] = f"{prevDayHPHC * 0.001:.3f}"

                        if status["yesterday"] == 0:
                            status["yesterday"] = prevDayHPHC

                        currWk = data.getCurrentWeek().getValue() * 0.001
                        currWkLastYear = (
                            data.getCurrentWeekLastYear().getValue() * 0.001
                        )
                        lastMonth = data.getLastMonth().getValue() * 0.001
                        lastMonthLastYear = (
                            data.getLastMonthLastYear().getValue() * 0.001
                        )
                        currMonth = data.getCurrentMonth().getValue() * 0.001
                        currMonthLastYear = (
                            data.getCurrentMonthLastYear().getValue() * 0.001
                        )
                        lastYear = data.getLastYear().getValue() * 0.001
                        currYear = data.getCurrentYear().getValue() * 0.001

                        dateDeb = data.getCurrentWeek().getDateDeb()

                        status["current_week"] = f"{currWk:.3f}"

                        if dateDeb is not None:
                            status[
                                "current_week_number"
                            ] = datetime.datetime.fromisoformat(dateDeb).isocalendar()[
                                1
                            ]

                        status["current_week_last_year"] = f"{currWkLastYear:.3f}"
                        status["last_month"] = f"{lastMonth:.3f}"
                        status["last_month_last_year"] = f"{lastMonthLastYear:.3f}"
                        status["current_month"] = f"{currMonth:.3f}"
                        status["current_month_last_year"] = f"{currMonthLastYear:.3f}"
                        status["last_year"] = f"{lastYear:.3f}"
                        status["current_year"] = f"{currYear:.3f}"

                        status["errorLastCall"] = data.getCardErrorLastCall()
                        status["errorLastCallInterne"] = data.getErrorLastCall()

                        if (
                            (lastYear is not None)
                            and (lastYear != 0)
                            and (currYear is not None)
                        ):
                            valeur = (
                                100
                                * (currYear - lastYear)
                                / lastYear
                            )
                            status["year_evolution"] = f"{valeur:.3f}"
                        else:
                            status["year_evolution"] = 0

                        if (
                            (lastMonthLastYear is not None)
                            and (lastMonthLastYear != 0)
                            and (lastMonth is not None)
                        ):
                            valeur = (
                                100
                                * (lastMonth - lastMonthLastYear)
                                / lastMonthLastYear
                            )
                            status["monthly_evolution"] = f"{valeur:.3f}"
                        else:
                            status["monthly_evolution"] = 0

                        if (
                            (currWkLastYear is not None)
                            and (currWkLastYear != 0)
                            and (currWk is not None)
                        ):
                            valeur = 100 * (currWk - currWkLastYear) / currWkLastYear
                            status["current_week_evolution"] = f"{valeur:.3f}"
                        else:
                            status["current_week_evolution"] = 0

                        if (
                            (currMonthLastYear is not None)
                            and (currMonthLastYear != 0)
                            and (currMonth is not None)
                        ):
                            valeur = (
                                100
                                * (currMonth - currMonthLastYear)
                                / currMonthLastYear
                            )
                            status["current_month_evolution"] = f"{valeur:.3f}"
                        else:
                            status["current_month_evolution"] = 0

                        yesterdayLastYear = data.getYesterdayLastYear().getValue()
                        yesterday = data.getYesterday().getValue()

                        if (
                            (yesterdayLastYear is not None)
                            and (yesterdayLastYear != 0)
                            and (yesterday is not None)
                        ):
                            if yesterday == 0 and prevDayHPHC != 0:
                                yestValue = prevDayHPHC
                            else:
                                yestValue = yesterday
                            valeur = (
                                (yestValue - yesterdayLastYear) / yesterdayLastYear
                            ) * 100
                            status["yesterday_evolution"] = f"{valeur:.3f}"
                        else:
                            status["yesterday_evolution"] = 0
                        status["subscribed_power"] = data.contract.getsubscribed_power()
                        status[
                            "offpeak_hours_enedis"
                        ] = data.contract.getoffpeak_hours()
                        status["offpeak_hours"] = data.contract.getHeuresCreuses()
                    if typeSensor == _production:
                        status[
                            "yesterday_production"
                        ] = data.getProductionYesterday().getValue()
                        status["errorLastCall"] = data.getCardErrorLastCall()
                        status["errorLastCallInterne"] = data.getErrorLastCall()
                        status["lastUpdate"] = data.getLastUpdate()
                        status["timeLastCall"] = data.getTimeLastCall()
                    if status["yesterday"] is None:
                        status["yesterday"] = 0
                    if status["yesterday_production"] is None:
                        status["yesterday_production"] = 0
                    if typeSensor == _consommation:  # data.isConsommation():
                        valeurstate = (
                            float(status["yesterday"]) * 0.001  # type:ignore[arg-type]
                        )
                    else:
                        valeurstate = (
                            float(
                                status["yesterday_production"]  # type:ignore[arg-type]
                            )
                            * 0.001
                        )
                    state = f"{valeurstate:.3f}"

                except Exception:
                    status["errorLastCall"] = data.getCardErrorLastCall()
                    status["errorLastCallInterne"] = data.getErrorLastCall()
                    self._LOGGER.error("-" * 60)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    self._LOGGER.error(sys.exc_info())
                    msg = repr(
                        traceback.format_exception(exc_type, exc_value, exc_traceback)
                    )

                    self._LOGGER.error(msg)
                    self._LOGGER.error("errorLastCall : %s ", data.getErrorLastCall())
            else:
                status["errorLastCall"] = data.getCardErrorLastCall()
                status["errorLastCallInterne"] = data.getErrorLastCall()
        else:
            status["errorLastCall"] = data.getCardErrorLastCall()
            status["errorLastCallInterne"] = data.getErrorLastCall()
        self._LOGGER.info("*** SENSOR ***")
        self._LOGGER.info("status :%s", status)
        self._LOGGER.info("state :%s", state)
        self._LOGGER.info("*** FIN SENSOR ***")
        return status, state
