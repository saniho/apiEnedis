from collections import defaultdict
import datetime
import sys, traceback

try:
    from .const import _consommation, _production

except ImportError:
    from const import _consommation, _production

__nameManageSensorState__ = "manageSensorState"
import logging


class manageSensorState:
    def __init__(self):
        self._init = False
        pass

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
        pass

    def get_PDL_ID(self):
        return self._myDataEnedis.getContract().get_PDL_ID()

    def getStatusYesterdayCost(self):
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        dataAvailable = False
        yesterdayDate = None
        if self._myDataEnedis.getContract() is not None:
            # if self._myDataEnedis.getYesterday().getValue() != 0: # on a eut des données
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
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        clefDate = laDate.strftime("%Y-%m-%d %H")
        status_counts["DateHeure"] = clefDate
        status_counts["detail"] = detail
        if self._myDataEnedis.getContract() is not None:
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
        import packaging.version

        if (versionCurrent is None) or (versionGit is None):
            return False
        elif packaging.version.parse(versionCurrent) < packaging.version.parse(
            versionGit
        ):
            return True
        else:
            return False

    def getStatusEnergy(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts = defaultdict(int)
        if self._myDataEnedis.getTimeLastCall() is not None:
            state = "{:.3f}".format(
                self._myDataEnedis.getCurrentYear().getValue() * 0.001
            )

        return status_counts, state

    def getStatusEnergyDetailHours(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts = defaultdict(int)
        # "last_reset": "2021-01-01T00:00:00",  # à corriger plus tard !!

        laDate = datetime.datetime.today() - datetime.timedelta(2)
        laDate = laDate.replace(minute=0, second=0, microsecond=0)
        lastReset = laDate
        if self._myDataEnedis.getTimeLastCall() is not None:
            DateHeureDetail = {}
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
            state = "{:.3f}".format(0.001 * total)
        lastResetIso = lastReset.isoformat()
        return lastResetIso, status_counts, state

    def getStatusEnergyDetailHoursCost(self, typeSensor=_consommation):
        state = "unavailable"
        status_counts = defaultdict(int)
        # "last_reset": "2021-01-01T00:00:00",  # à corriger plus tard !!

        laDate = datetime.datetime.today() - datetime.timedelta(2)
        laDate = laDate.replace(minute=0, second=0, microsecond=0)
        lastReset = laDate
        if self._myDataEnedis.getTimeLastCall() is not None:
            DateHeureDetail = {}
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

            costHC = "{:.3f}".format(0.001 * self._myDataEnedis.getHCCost(valeurHC))
            costHP = "{:.3f}".format(0.001 * self._myDataEnedis.getHPCost(valeurHP))
            cost = self._myDataEnedis.getHCCost(
                valeurHC
            ) + self._myDataEnedis.getHPCost(valeurHP)
            state = "{:.3f}".format(0.001 * cost)
        lastResetIso = lastReset.isoformat()
        return lastResetIso, status_counts, state

    def getStatus(self, typeSensor=_consommation):
        # Raccourci pour self._myDataEnedit (lignes plus court)
        data = self._myDataEnedis

        state = "unavailable"
        status = defaultdict(int)
        status["version"] = self.version
        status["versionGit"] = data.getGitVersion()
        status["versionUpdateAvailable"] = self.getExistsRecentVersion(
            self.version, data.getGitVersion()
        )

        if data.getTimeLastCall() is not None:
            self._LOGGER.info(
                "-- ** on va mettre à jour : %s" % data.getContract().get_PDL_ID()
            )
            status["nbCall"] = data.getNbCall()
            status["typeCompteur"] = typeSensor
            status["numPDL"] = data.getContract().get_PDL_ID()
            status["horaireMinCall"] = data.getHoraireMin()
            status["activationDate"] = data.getContract().getLastActivationDate()
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
                        listeClef = list(last7daysHP.keys())
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
                            status["day_%s_HP" % (niemejour)] = valeur
                        last7daysHC = data.getLast7DaysDetails().getDaysHC()
                        niemejour = 0
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = last7daysHC[clef]
                            status["day_%s_HC" % (niemejour)] = valeur
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
                                valeur = "{:.2f}".format(valeur)
                            cout.append(valeur)
                        status["dailyweek_cost"] = cout
                        niemejour = 0
                        coutHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = 0.001 * data.getHCCost(last7daysHC[clef])
                                valeur = "{:.2f}".format(valeur)
                            coutHC.append(valeur)
                        status["dailyweek_costHC"] = coutHC

                        niemejour = 0
                        dailyHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHC.keys():
                                valeur = "{:.3f}".format(0.001 * last7daysHC[clef])
                            dailyHC.append(valeur)
                        status["dailyweek_HC"] = dailyHC

                        status["dailyweek"] = [(day) for day in listeClef]
                        niemejour = 0
                        coutHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeur = 0.001 * data.getHPCost(last7daysHP[clef])
                                valeur = "{:.2f}".format(valeur)
                            coutHP.append(valeur)
                        status["dailyweek_costHP"] = coutHP
                        # gestion du format : "{:.2f}".format(a)

                        niemejour = 0
                        dailyHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeur = last7daysHP[clef]
                                valeur = "{:.3f}".format(0.001 * valeur)
                            dailyHP.append(valeur)
                        status["dailyweek_HP"] = dailyHP

                        niemejour = 0
                        daily = []
                        for clef in listeClef:
                            niemejour += 1
                            somme = -1
                            if (
                                clef in last7daysHP.keys()
                                and clef in last7daysHC.keys()
                            ):
                                somme = last7daysHP[clef] + last7daysHC[clef]
                                somme = "{:.2f}".format(0.001 * somme)
                            status["day_%s" % (niemejour)] = somme
                            daily.append(somme)
                        status["daily"] = daily

                        status["halfhourly"] = []
                        status["offpeak_hours"] = "{:.3f}".format(
                            data.getYesterdayHCHP().getHC() * 0.001
                        )
                        status["peak_hours"] = "{:.3f}".format(
                            data.getYesterdayHCHP().getHP() * 0.001
                        )
                        if (
                            data.getYesterdayHCHP().getHC()
                            + data.getYesterdayHCHP().getHP()
                        ) != 0:
                            valeur = (data.getYesterdayHCHP().getHP() * 100) / (
                                data.getYesterdayHCHP().getHC()
                                + data.getYesterdayHCHP().getHP()
                            )
                            status["peak_offpeak_percent"] = "{:.2f}".format(valeur)
                        else:
                            status["peak_offpeak_percent"] = 0
                        status["yesterday_HC_cost"] = "{:.3f}".format(
                            0.001 * data.getHCCost(data.getYesterdayHCHP().getHC())
                        )
                        status["yesterday_HP_cost"] = "{:.3f}".format(
                            0.001 * data.getHPCost(data.getYesterdayHCHP().getHP())
                        )
                        status["daily_cost"] = "{:.2f}".format(
                            0.001 * data.getHCCost(data.getYesterdayHCHP().getHC())
                            + 0.001 * data.getHPCost(data.getYesterdayHCHP().getHP())
                        )
                        status["yesterday_HC"] = "{:.3f}".format(
                            data.getYesterdayHCHP().getHC() * 0.001
                        )
                        status["yesterday_HP"] = "{:.3f}".format(
                            data.getYesterdayHCHP().getHP() * 0.001
                        )
                        status["yesterday_HCHP"] = "{:.3f}".format(
                            (
                                data.getYesterdayHCHP().getHC()
                                + data.getYesterdayHCHP().getHP()
                            )
                            * 0.001
                        )
                        if status["yesterday"] == 0:
                            status["yesterday"] = (
                                data.getYesterdayHCHP().getHC()
                                + data.getYesterdayHCHP().getHP()
                            )
                        status["current_week"] = "{:.3f}".format(
                            data.getCurrentWeek().getValue() * 0.001
                        )

                        if data.getCurrentWeek().getDateDeb() is not None:
                            status[
                                "current_week_number"
                            ] = datetime.datetime.fromisoformat(
                                data.getCurrentWeek().getDateDeb()
                            ).isocalendar()[
                                1
                            ]
                        status["current_week_last_year"] = "{:.3f}".format(
                            data.getCurrentWeekLastYear().getValue() * 0.001
                        )
                        status["last_month"] = "{:.3f}".format(
                            data.getLastMonth().getValue() * 0.001
                        )
                        status["last_month_last_year"] = "{:.3f}".format(
                            data.getLastMonthLastYear().getValue() * 0.001
                        )
                        status["current_month"] = "{:.3f}".format(
                            data.getCurrentMonth().getValue() * 0.001
                        )
                        status["current_month_last_year"] = "{:.3f}".format(
                            data.getCurrentMonthLastYear().getValue() * 0.001
                        )
                        status["last_year"] = "{:.3f}".format(
                            data.getLastYear().getValue() * 0.001
                        )
                        status["current_year"] = "{:.3f}".format(
                            data.getCurrentYear().getValue() * 0.001
                        )
                        status["errorLastCall"] = data.getCardErrorLastCall()
                        status["errorLastCallInterne"] = data.getErrorLastCall()
                        if (
                            (data.getLastMonthLastYear().getValue() is not None)
                            and (data.getLastMonthLastYear().getValue() != 0)
                            and (data.getLastMonth().getValue() is not None)
                        ):
                            valeur = (
                                (
                                    data.getLastMonth().getValue()
                                    - data.getLastMonthLastYear().getValue()
                                )
                                / data.getLastMonthLastYear().getValue()
                            ) * 100
                            status["monthly_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status["monthly_evolution"] = 0
                        if (
                            (data.getCurrentWeekLastYear().getValue() is not None)
                            and (data.getCurrentWeekLastYear().getValue() != 0)
                            and (data.getCurrentWeek().getValue() is not None)
                        ):
                            valeur = (
                                (
                                    data.getCurrentWeek().getValue()
                                    - data.getCurrentWeekLastYear().getValue()
                                )
                                / data.getCurrentWeekLastYear().getValue()
                            ) * 100
                            status["current_week_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status["current_week_evolution"] = 0
                        if (
                            (data.getCurrentMonthLastYear().getValue() is not None)
                            and (data.getCurrentMonthLastYear().getValue() != 0)
                            and (data.getCurrentMonth().getValue() is not None)
                        ):
                            valeur = (
                                (
                                    data.getCurrentMonth().getValue()
                                    - data.getCurrentMonthLastYear().getValue()
                                )
                                / data.getCurrentMonthLastYear().getValue()
                            ) * 100
                            status["current_month_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status["current_month_evolution"] = 0
                        if (
                            (data.getYesterdayLastYear().getValue() is not None)
                            and (data.getYesterdayLastYear().getValue() != 0)
                            and (data.getYesterday().getValue() is not None)
                        ):
                            valeur = (
                                (
                                    data.getYesterday().getValue()
                                    - data.getYesterdayLastYear().getValue()
                                )
                                / data.getYesterdayLastYear().getValue()
                            ) * 100
                            status["yesterday_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status["yesterday_evolution"] = 0
                        status[
                            "subscribed_power"
                        ] = data.getContract().getsubscribed_power()
                        status[
                            "offpeak_hours_enedis"
                        ] = data.getContract().getoffpeak_hours()
                        status["offpeak_hours"] = data.getContract().getHeuresCreuses()
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
                        valeurstate = status["yesterday"] * 0.001
                    else:
                        valeurstate = status["yesterday_production"] * 0.001
                    state = "{:.3f}".format(valeurstate)

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
                    self._LOGGER.error(
                        "errorLastCall : %s " % (data.getErrorLastCall())
                    )
            else:
                status["errorLastCall"] = data.getCardErrorLastCall()
                status["errorLastCallInterne"] = data.getErrorLastCall()
        else:
            status["errorLastCall"] = data.getCardErrorLastCall()
            status["errorLastCallInterne"] = data.getErrorLastCall()

        return status, state


def logSensorState(status_counts):
    for x in status_counts.keys():
        print(" %s : %s" % (x, status_counts[x]))
