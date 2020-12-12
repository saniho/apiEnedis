from collections import defaultdict
import datetime

def manageSensorState( _myDataEnedis,_LOGGER = None, version = None ):
    status_counts = defaultdict(int)
    status_counts["version"] = version
    _myDataEnedis.update()
    if ( not _myDataEnedis.getUpdateRealise()):
        # si pas de mises à jour alors juste return !!
        return
    if (_myDataEnedis.getStatusLastCall()):  # update avec statut ok
        if( 1 ): #
        #try:
            status_counts["typeCompteur"] = _myDataEnedis.getTypePDL()
            if ( _myDataEnedis.isConsommation()):
                status_counts["lastSynchro"] = datetime.datetime.now()
                status_counts["lastUpdate"] = _myDataEnedis.getLastUpdate()
                status_counts["timeLastCall"] = _myDataEnedis.getTimeLastCall()
                # à supprimer car doublon avec j_1
                status_counts['yesterday'] = _myDataEnedis.getYesterday()
                status_counts['last_week'] = _myDataEnedis.getLastWeek()

                #last7days = _myDataEnedis.getLast7Days()
                #for day in last7days:
                #    status_counts['day_%s' % (day["niemejour"])] = day["value"]
                #status_counts['daily'] = [("{:.2f}".format(day["value"] * 0.001)) for day in last7days]

                last7daysHP = _myDataEnedis.get7DaysHP()
                listeClef = list(last7daysHP.keys())
                listeClef.reverse()

                today = datetime.date.today()
                listeClef = []
                for i in range( 7 ):
                    maDate = today - datetime.timedelta( i + 1)
                    listeClef.append(maDate.strftime("%Y-%m-%d"))
                niemejour = 0
                for clef in listeClef:
                    niemejour += 1
                    valeur= -1
                    if ( clef in last7daysHP.keys()):
                        valeur = last7daysHP[clef]
                    status_counts['day_%s_HP' % (niemejour)] = valeur
                last7daysHC = _myDataEnedis.get7DaysHC()
                #listeClef = list(last7daysHP.keys())
                #listeClef.reverse()
                niemejour = 0
                for clef in listeClef:
                    # print(clef, " ", last7daysHC[clef])
                    niemejour += 1
                    valeur= -1
                    if ( clef in last7daysHC.keys()):
                        valeur = last7daysHC[clef]
                    status_counts['day_%s_HC' % (niemejour)] = valeur
                # gestion du cout par jour ....

                niemejour = 0
                cout = []
                for clef in listeClef:
                    niemejour += 1
                    valeur = -1
                    if ( clef in last7daysHC.keys() and clef in last7daysHP.keys()):
                        valeur = 0.001 * _myDataEnedis.getHCCost(last7daysHC[clef]) + \
                                0.001 * _myDataEnedis.getHPCost(last7daysHP[clef])
                        valeur = "{:.2f}".format(valeur)
                    cout.append(valeur)
                status_counts['dailyweek_cost'] = cout
                niemejour = 0
                coutHC = []
                for clef in listeClef:
                    niemejour += 1
                    valeur = -1
                    if ( clef in last7daysHC.keys()):
                        valeur = 0.001 * _myDataEnedis.getHCCost(last7daysHC[clef])
                        valeur = "{:.2f}".format(valeur)
                    coutHC.append(valeur)
                status_counts['dailyweek_costHC'] = coutHC

                niemejour = 0
                dailyHC = []
                for clef in listeClef:
                    niemejour += 1
                    valeur = -1
                    if ( clef in last7daysHC.keys()):
                        valeur = "{:.3f}".format(0.001 * last7daysHC[clef])
                    dailyHC.append(valeur)
                status_counts['dailyweek_HC'] = dailyHC

                status_counts['dailyweek'] = [(day) for day in listeClef]
                niemejour = 0
                coutHP = []
                for clef in listeClef:
                    niemejour += 1
                    valeur = -1
                    if ( clef in last7daysHP.keys()):
                        valeur = 0.001 * _myDataEnedis.getHPCost(last7daysHP[clef])
                        valeur = "{:.2f}".format(valeur)
                    coutHP.append(valeur)
                status_counts['dailyweek_costHP'] = coutHP
                #gestion du format : "{:.2f}".format(a)

                niemejour = 0
                dailyHP = []
                for clef in listeClef:
                    niemejour += 1
                    valeur = -1
                    if ( clef in last7daysHP.keys()):
                        valeur = last7daysHP[clef]
                        valeur = "{:.3f}".format(0.001 * valeur)
                    dailyHP.append(valeur)
                status_counts['dailyweek_HP'] = dailyHP

                niemejour = 0
                daily = []
                for clef in listeClef:
                    niemejour += 1
                    somme = -1
                    if ( clef in last7daysHP.keys() and clef in last7daysHC.keys() ):
                        somme = last7daysHP[clef] + last7daysHC[clef]
                        somme = "{:.2f}".format(0.001 * somme)
                    status_counts['day_%s' %(niemejour)] = somme
                    daily.append(somme)
                status_counts['daily'] = daily

                status_counts["halfhourly"] = []
                status_counts["offpeak_hours"] = "{:.3f}".format(_myDataEnedis.getYesterdayHC() * 0.001 )
                status_counts["peak_hours"] = "{:.3f}".format(_myDataEnedis.getYesterdayHP() * 0.001 )
                if ((_myDataEnedis.getYesterdayHC() + _myDataEnedis.getYesterdayHP()) != 0):
                    valeur = (_myDataEnedis.getYesterdayHP() * 100) / \
                            ( _myDataEnedis.getYesterdayHC() + _myDataEnedis.getYesterdayHP())
                    status_counts["peak_offpeak_percent"] = "{:.2f}".format(valeur)
                else:
                    status_counts["peak_offpeak_percent"] = 0
                status_counts["yesterday_HC_cost"] = \
                    "{:.3f}".format(0.001 * _myDataEnedis.getHCCost( _myDataEnedis.getYesterdayHC()))
                status_counts["yesterday_HP_cost"] = \
                    "{:.3f}".format(0.001 * _myDataEnedis.getHPCost( _myDataEnedis.getYesterdayHP()))
                status_counts["daily_cost"] = "{:.2f}".format(
                                            0.001 * _myDataEnedis.getHCCost( _myDataEnedis.getYesterdayHC()) + \
                                            0.001 * _myDataEnedis.getHPCost( _myDataEnedis.getYesterdayHP())
                                            )
                status_counts["yesterday_HC"] = "{:.3f}".format(_myDataEnedis.getYesterdayHC() * 0.001 )
                status_counts["yesterday_HP"] = "{:.3f}".format(_myDataEnedis.getYesterdayHP() * 0.001 )
                status_counts['current_week'] = "{:.3f}".format(_myDataEnedis.getCurrentWeek() * 0.001 )
                status_counts['last_month'] = "{:.3f}".format(_myDataEnedis.getLastMonth() * 0.001 )
                status_counts['current_month'] = "{:.3f}".format(_myDataEnedis.getCurrentMonth() * 0.001 )
                status_counts['last_year'] = "{:.3f}".format(_myDataEnedis.getLastYear() * 0.001 )
                status_counts['current_year'] = "{:.3f}".format(_myDataEnedis.getCurrentYear() * 0.001 )
                status_counts['errorLastCall'] = _myDataEnedis.getErrorLastCall()
                if ((_myDataEnedis.getLastMonthLastYear() is not None) and
                        (_myDataEnedis.getLastMonthLastYear() != 0) and
                        (_myDataEnedis.getLastMonth() is not None)):
                    valeur = \
                        ((_myDataEnedis.getLastMonth() - _myDataEnedis.getLastMonthLastYear())
                         / _myDataEnedis.getLastMonthLastYear()) * 100
                    status_counts["monthly_evolution"] = "{:.3f}".format(valeur)
                else:
                    status_counts["monthly_evolution"] = 0
                status_counts["subscribed_power"] = _myDataEnedis.getsubscribed_power()
                status_counts["offpeak_hours_information"] = _myDataEnedis.getoffpeak_hours()
                # status_counts['yesterday'] = ""
            elif( _myDataEnedis.isProduction()):
                status_counts["yesterday_production"] = _myDataEnedis.getProductionYesterday()
                status_counts['errorLastCall'] = _myDataEnedis.getErrorLastCall()
                status_counts["lastSynchro"] = datetime.datetime.now()
                status_counts["lastUpdate"] = _myDataEnedis.getLastUpdate()
                status_counts["timeLastCall"] = _myDataEnedis.getTimeLastCall()


        """except:
            status_counts['errorLastCall'] = _myDataEnedis.getErrorLastCall()
            _LOGGER.warning( "errorLastCall : %s " %( _myDataEnedis.getErrorLastCall() ))
        """
    return status_counts

def logSensorState( status_counts ):
    for x in status_counts.keys():
        print(" %s : %s" %( x, status_counts[x]))