from collections import defaultdict
import datetime
import sys, traceback

try:
    from .const import (
        _consommation,
        _production
    )

except ImportError:
    from const import (
        _consommation,
        _production
    )

__nameManageSensorState__ = "manageSensorState"
import logging

class manageSensorState:
    def __init__(self ):
        self._init = False
        pass
    def getInit(self):
        return self._init
    def setInit(self, val):
        self._init = val
    def init( self, _myDataEnedis, _LOGGER = None, version = None ):
        # enedis à initialiser ici!!!
        self._myDataEnedis = _myDataEnedis
        if _LOGGER == None:
            _LOGGER = logging.getLogger(__nameManageSensorState__)
        self._LOGGER =  _LOGGER
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
        if self._myDataEnedis.getContract() != None:
            if self._myDataEnedis.getYesterday().getValue() != 0: # on a eut des données
                status_counts["yesterday_HC_cost"] = \
                    "{:.3f}".format(0.001 *
                        self._myDataEnedis.getHCCost(self._myDataEnedis.getYesterdayHCHP().getHC()))
                status_counts["yesterday_HP_cost"] = \
                    "{:.3f}".format(0.001 *
                        self._myDataEnedis.getHPCost(self._myDataEnedis.getYesterdayHCHP().getHP()))
                daily_cost = "{:.2f}".format(
                    0.001 *
                        self._myDataEnedis.getHCCost(self._myDataEnedis.getYesterdayHCHP().getHC()) + \
                    0.001 *
                        self._myDataEnedis.getHPCost(self._myDataEnedis.getYesterdayHCHP().getHP())
                )
                yesterdayDate = self._myDataEnedis.getYesterday().getDateDeb()
                status_counts["daily_cost"] = daily_cost
                state = daily_cost
                dataAvailable = True
        return dataAvailable, yesterdayDate, status_counts, state

    def getStatusHistory(self, laDate, detail = "ALL", typeSensor = _consommation):
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        clefDate = laDate.strftime("%Y-%m-%d %H" )
        status_counts["DateHeure"] = clefDate
        status_counts["detail"] = detail
        if self._myDataEnedis.getContract() != None:
            if self._myDataEnedis.isConsommation():
                state = 0
                DateHeureDetail = {}
                if ( detail == "ALL"):
                    DateHeureDetail = self._myDataEnedis.getLast7DaysDetails().getDateHeureDetail()
                if ( detail == "HP"):
                    DateHeureDetail = self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHP()
                if ( detail == "HC"):
                    DateHeureDetail = self._myDataEnedis.getLast7DaysDetails().getDateHeureDetailHC()
                if ( clefDate in DateHeureDetail.keys()):
                    state = DateHeureDetail[clefDate] * 0.001
        return status_counts, state

    def getExistsRecentVersion(self, versionCurrent, versionGit):
        import packaging.version
        if ( versionCurrent is None ) or ( versionGit is None ):
            return False
        elif ( packaging.version.parse(versionCurrent) < packaging.version.parse(versionGit)):
            return True
        else:
            return False

    def getStatus(self, typeSensor = _consommation):
        state = "unavailable"
        status_counts = defaultdict(int)
        status_counts["version"] = self.version
        status_counts["versionGit"] = self._myDataEnedis.getGitVersion()
        status_counts["versionUpdateAvailable"] = \
            self.getExistsRecentVersion( self.version, self._myDataEnedis.getGitVersion() )

        if self._myDataEnedis.getTimeLastCall() != None:
            self._LOGGER.info("-- ** on va mettre à jour : %s" %self._myDataEnedis.getContract().get_PDL_ID())
            status_counts["nbCall"] = self._myDataEnedis.getNbCall()
            status_counts["typeCompteur"] = typeSensor
            status_counts["numPDL"] = self._myDataEnedis.getContract().get_PDL_ID()
            status_counts["horaireMinCall"] = self._myDataEnedis.getHoraireMin()
            status_counts["activationDate"] = self._myDataEnedis.getContract().getLastActivationDate()
            if self._myDataEnedis.isConsommation():
                status_counts["lastUpdate"] = self._myDataEnedis.getLastUpdate()
                status_counts["timeLastCall"] = self._myDataEnedis.getTimeLastCall()
                # à supprimer car doublon avec j_1
                status_counts['yesterday'] = self._myDataEnedis.getYesterday().getValue()
                status_counts['last_week'] = self._myDataEnedis.getLastWeek().getValue()

            if (1):#self._myDataEnedis.getStatusLastCall():  # update avec statut ok
                try:
                    # typesensor ... fonction de  ?
                    if typeSensor == _consommation: #self._myDataEnedis.isConsommation():

                        status_counts["lastUpdate"] = self._myDataEnedis.getLastUpdate()
                        status_counts["timeLastCall"] = self._myDataEnedis.getTimeLastCall()
                        # à supprimer car doublon avec j_1
                        status_counts['yesterday'] = self._myDataEnedis.getYesterday().getValue()
                        status_counts['yesterdayDate'] = self._myDataEnedis.getYesterday().getDateDeb()
                        status_counts['yesterdayLastYear'] = self._myDataEnedis.getYesterdayLastYear().getValue()
                        status_counts['yesterdayLastYearDate'] = self._myDataEnedis.getYesterday().getDateDeb()
                        status_counts['yesterdayConsumptionMaxPower'] = \
                            self._myDataEnedis.getYesterdayConsumptionMaxPower().getValue()
                        status_counts['last_week'] = self._myDataEnedis.getLastWeek().getValue()
                        last7daysHP = self._myDataEnedis.getLast7DaysDetails().getDaysHP()
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
                            status_counts['day_%s_HP' % (niemejour)] = valeur
                        last7daysHC = self._myDataEnedis.getLast7DaysDetails().getDaysHC()
                        niemejour = 0
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (clef in last7daysHC.keys()):
                                valeur = last7daysHC[clef]
                            status_counts['day_%s_HC' % (niemejour)] = valeur
                        # gestion du cout par jour ....

                        niemejour = 0
                        cout = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (clef in last7daysHC.keys() and clef in last7daysHP.keys()):
                                valeur = 0.001 * self._myDataEnedis.getHCCost(last7daysHC[clef]) + \
                                         0.001 * self._myDataEnedis.getHPCost(last7daysHP[clef])
                                valeur = "{:.2f}".format(valeur)
                            cout.append(valeur)
                        status_counts['dailyweek_cost'] = cout
                        niemejour = 0
                        coutHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (clef in last7daysHC.keys()):
                                valeur = 0.001 * self._myDataEnedis.getHCCost(last7daysHC[clef])
                                valeur = "{:.2f}".format(valeur)
                            coutHC.append(valeur)
                        status_counts['dailyweek_costHC'] = coutHC

                        niemejour = 0
                        dailyHC = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (clef in last7daysHC.keys()):
                                valeur = "{:.3f}".format(0.001 * last7daysHC[clef])
                            dailyHC.append(valeur)
                        status_counts['dailyweek_HC'] = dailyHC

                        status_counts['dailyweek'] = [(day) for day in listeClef]
                        niemejour = 0
                        coutHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if clef in last7daysHP.keys():
                                valeur = 0.001 * self._myDataEnedis.getHPCost(last7daysHP[clef])
                                valeur = "{:.2f}".format(valeur)
                            coutHP.append(valeur)
                        status_counts['dailyweek_costHP'] = coutHP
                        # gestion du format : "{:.2f}".format(a)

                        niemejour = 0
                        dailyHP = []
                        for clef in listeClef:
                            niemejour += 1
                            valeur = -1
                            if (clef in last7daysHP.keys()):
                                valeur = last7daysHP[clef]
                                valeur = "{:.3f}".format(0.001 * valeur)
                            dailyHP.append(valeur)
                        status_counts['dailyweek_HP'] = dailyHP

                        niemejour = 0
                        daily = []
                        for clef in listeClef:
                            niemejour += 1
                            somme = -1
                            if (clef in last7daysHP.keys() and clef in last7daysHC.keys()):
                                somme = last7daysHP[clef] + last7daysHC[clef]
                                somme = "{:.2f}".format(0.001 * somme)
                            status_counts['day_%s' % (niemejour)] = somme
                            daily.append(somme)
                        status_counts['daily'] = daily

                        status_counts["halfhourly"] = []
                        status_counts["offpeak_hours"] = \
                            "{:.3f}".format(self._myDataEnedis.getYesterdayHCHP().getHC() * 0.001)
                        status_counts["peak_hours"] = \
                            "{:.3f}".format(self._myDataEnedis.getYesterdayHCHP().getHP() * 0.001)
                        if (self._myDataEnedis.getYesterdayHCHP().getHC() + self._myDataEnedis.getYesterdayHCHP().getHP()) != 0:
                            valeur = (self._myDataEnedis.getYesterdayHCHP().getHP() * 100) / \
                                     (self._myDataEnedis.getYesterdayHCHP().getHC() +
                                      self._myDataEnedis.getYesterdayHCHP().getHP() )
                            status_counts["peak_offpeak_percent"] = "{:.2f}".format(valeur)
                        else:
                            status_counts["peak_offpeak_percent"] = 0
                        status_counts["yesterday_HC_cost"] = \
                            "{:.3f}".format(0.001 *
                                self._myDataEnedis.getHCCost(self._myDataEnedis.getYesterdayHCHP().getHC()))
                        status_counts["yesterday_HP_cost"] = \
                            "{:.3f}".format(0.001 *
                                self._myDataEnedis.getHPCost(self._myDataEnedis.getYesterdayHCHP().getHP()))
                        status_counts["daily_cost"] = "{:.2f}".format(
                            0.001 * self._myDataEnedis.getHCCost(self._myDataEnedis.getYesterdayHCHP().getHC()) + \
                            0.001 * self._myDataEnedis.getHPCost(self._myDataEnedis.getYesterdayHCHP().getHP())
                        )
                        status_counts["yesterday_HC"] = \
                            "{:.3f}".format(self._myDataEnedis.getYesterdayHCHP().getHC() * 0.001)
                        status_counts["yesterday_HP"] = \
                            "{:.3f}".format(self._myDataEnedis.getYesterdayHCHP().getHP() * 0.001)
                        status_counts['current_week'] = \
                            "{:.3f}".format(self._myDataEnedis.getCurrentWeek().getValue() * 0.001)

                        if self._myDataEnedis.getCurrentWeek().getDateDeb() != None:
                            status_counts['current_week_number'] = \
                                datetime.datetime.fromisoformat(self._myDataEnedis.getCurrentWeek().getDateDeb()).isocalendar()[1]
                        status_counts['current_week_last_year'] = \
                            "{:.3f}".format(self._myDataEnedis.getCurrentWeekLastYear().getValue() * 0.001)
                        status_counts['last_month'] = "{:.3f}".format(self._myDataEnedis.getLastMonth().getValue() * 0.001)
                        status_counts['last_month_last_year'] = \
                            "{:.3f}".format(self._myDataEnedis.getLastMonthLastYear().getValue() * 0.001)
                        status_counts['current_month'] = \
                            "{:.3f}".format(self._myDataEnedis.getCurrentMonth().getValue() * 0.001)
                        status_counts['current_month_last_year'] = \
                            "{:.3f}".format(self._myDataEnedis.getCurrentMonthLastYear().getValue() * 0.001)
                        status_counts['last_year'] = "{:.3f}".format(self._myDataEnedis.getLastYear().getValue() * 0.001)
                        status_counts['current_year'] = "{:.3f}".format(self._myDataEnedis.getCurrentYear().getValue() * 0.001)
                        status_counts['errorLastCall'] = self._myDataEnedis.getCardErrorLastCall()
                        status_counts['errorLastCallInterne'] = self._myDataEnedis.getErrorLastCall()
                        if ((self._myDataEnedis.getLastMonthLastYear().getValue() is not None) and
                                (self._myDataEnedis.getLastMonthLastYear().getValue() != 0) and
                                (self._myDataEnedis.getLastMonth().getValue() is not None)):
                            valeur = \
                                ((self._myDataEnedis.getLastMonth().getValue() -
                                  self._myDataEnedis.getLastMonthLastYear().getValue())
                                 / self._myDataEnedis.getLastMonthLastYear().getValue()) * 100
                            status_counts["monthly_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status_counts["monthly_evolution"] = 0
                        if ((self._myDataEnedis.getCurrentWeekLastYear().getValue() is not None) and
                                (self._myDataEnedis.getCurrentWeekLastYear().getValue() != 0) and
                                (self._myDataEnedis.getCurrentWeek().getValue() is not None)):
                            valeur = \
                                ((self._myDataEnedis.getCurrentWeek().getValue() -
                                  self._myDataEnedis.getCurrentWeekLastYear().getValue())
                                 / self._myDataEnedis.getCurrentWeekLastYear().getValue()) * 100
                            status_counts["current_week_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status_counts["current_week_evolution"] = 0
                        if ((self._myDataEnedis.getCurrentMonthLastYear().getValue() is not None) and
                                (self._myDataEnedis.getCurrentMonthLastYear().getValue() != 0) and
                                (self._myDataEnedis.getCurrentMonth().getValue() is not None)):
                            valeur = \
                                ((self._myDataEnedis.getCurrentMonth().getValue() -
                                  self._myDataEnedis.getCurrentMonthLastYear().getValue())
                                 / self._myDataEnedis.getCurrentMonthLastYear().getValue()) * 100
                            status_counts["current_month_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status_counts["current_month_evolution"] = 0
                        if ((self._myDataEnedis.getYesterdayLastYear().getValue() is not None) and
                                (self._myDataEnedis.getYesterdayLastYear().getValue() != 0) and
                                (self._myDataEnedis.getYesterday().getValue() is not None)):
                            valeur = \
                                ((self._myDataEnedis.getYesterday().getValue() - self._myDataEnedis.getYesterdayLastYear().getValue())
                                 / self._myDataEnedis.getYesterdayLastYear().getValue()) * 100
                            status_counts["yesterday_evolution"] = "{:.3f}".format(valeur)
                        else:
                            status_counts["yesterday_evolution"] = 0
                        status_counts["subscribed_power"] = self._myDataEnedis.getContract().getsubscribed_power()
                        status_counts["offpeak_hours_enedis"] = self._myDataEnedis.getContract().getoffpeak_hours()
                        status_counts["offpeak_hours"] = self._myDataEnedis.getContract().getHeuresCreuses()
                        # status_counts['yesterday'] = ""
                    if typeSensor == _production: #self._myDataEnedis.isProduction():
                        status_counts["yesterday_production"] = self._myDataEnedis.getProductionYesterday().getValue()
                        status_counts['errorLastCall'] = self._myDataEnedis.getCardErrorLastCall()
                        status_counts['errorLastCallInterne'] = self._myDataEnedis.getErrorLastCall()
                        status_counts["lastUpdate"] = self._myDataEnedis.getLastUpdate()
                        status_counts["timeLastCall"] = self._myDataEnedis.getTimeLastCall()
                    if status_counts['yesterday'] == None:
                        status_counts['yesterday'] = 0
                    if status_counts['yesterday_production'] == None:
                        status_counts['yesterday_production'] = 0
                    if typeSensor == _consommation: #self._myDataEnedis.isConsommation():
                        valeurstate = status_counts['yesterday'] * 0.001
                    else:
                        valeurstate = status_counts['yesterday_production'] * 0.001
                    state = "{:.3f}".format(valeurstate)

                except Exception:
                    status_counts['errorLastCall'] = self._myDataEnedis.getCardErrorLastCall()
                    status_counts['errorLastCallInterne'] = self._myDataEnedis.getErrorLastCall()
                    self._LOGGER.error("-" * 60)
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    self._LOGGER.error(sys.exc_info())
                    msg = repr(traceback.format_exception(exc_type, exc_value,
                                                          exc_traceback))

                    self._LOGGER.error(msg)
                    self._LOGGER.error("errorLastCall : %s " % (self._myDataEnedis.getErrorLastCall()))
            else:
                status_counts['errorLastCall'] = self._myDataEnedis.getCardErrorLastCall()
                status_counts['errorLastCallInterne'] = self._myDataEnedis.getErrorLastCall()
        else:
            status_counts['errorLastCall'] = self._myDataEnedis.getCardErrorLastCall()
            status_counts['errorLastCallInterne'] = self._myDataEnedis.getErrorLastCall()

        return status_counts, state

def logSensorState( status_counts ):
    for x in status_counts.keys():
        print(" %s : %s" %( x, status_counts[x]))