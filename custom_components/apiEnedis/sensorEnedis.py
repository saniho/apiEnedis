from collections import defaultdict
import datetime

def manageSensorState( _myDataEnedis,_LOGGER = None ):
    status_counts = defaultdict(int)
    _myDataEnedis.update()
    if (_myDataEnedis.getStatusLastCall()):  # update avec statut ok
        try:
            status_counts["lastSynchro"] = datetime.datetime.now()
            status_counts["lastUpdate"] = _myDataEnedis.getLastUpdate()
            status_counts["timeLastCall"] = _myDataEnedis.getTimeLastCall()
            # à supprimer car doublon avec j_1
            status_counts['yesterday'] = _myDataEnedis.getYesterday()
            status_counts['last_week'] = _myDataEnedis.getLastWeek()

            last7days = _myDataEnedis.getLast7Days()
            for day in last7days:
                status_counts['day_%s' % (day["niemejour"])] = day["value"]
            status_counts['daily'] = [(day["value"] * 0.001) for day in last7days]

            last7daysHP = _myDataEnedis.get7DaysHP()
            listeClef = list(last7daysHP.keys())
            listeClef.reverse()
            niemejour = 0
            for clef in listeClef:
                niemejour += 1
                status_counts['day_%s_HP' % (niemejour)] = last7daysHP[clef]
            last7daysHC = _myDataEnedis.get7DaysHC()
            listeClef = list(last7daysHP.keys())
            listeClef.reverse()
            niemejour = 0
            for clef in listeClef:
                # print(clef, " ", last7daysHC[clef])
                niemejour += 1
                status_counts['day_%s_HC' % (niemejour)] = last7daysHC[clef]
            # gestion du cout par jour ....

            niemejour = 0
            cout = []
            for clef in listeClef:
                niemejour += 1
                cout.append(0.001 * _myDataEnedis.getHCCost(last7daysHC[clef]) +
                            0.001 * _myDataEnedis.getHPCost(last7daysHP[clef]))
            status_counts['dailyweek_cost'] = [("{:.2f}".format(day_cost))  for day_cost in cout]
            niemejour = 0
            coutHC = []
            for clef in listeClef:
                niemejour += 1
                coutHC.append(
                    0.001 * _myDataEnedis.getHCCost(last7daysHC[clef]))
            status_counts['dailyweek_costHC'] = [("{:.2f}".format(day_cost))  for day_cost in coutHC]

            niemejour = 0
            dailyHC = []
            for clef in listeClef:
                niemejour += 1
                dailyHC.append(last7daysHC[clef])
            status_counts['dailyweek_HC'] = [("{:.3f}".format(0.001 * day_HC)) for day_HC in dailyHC]

            status_counts['dailyweek'] = [(day) for day in listeClef]
            niemejour = 0
            coutHP = []
            for clef in listeClef:
                niemejour += 1
                coutHP.append(
                    0.001 * _myDataEnedis.getHPCost(last7daysHP[clef]))
            status_counts['dailyweek_costHP'] = [("{:.2f}".format(day_cost)) for day_cost in coutHP]
            #gestion du format : "{:.2f}".format(a)

            niemejour = 0
            dailyHP = []
            for clef in listeClef:
                niemejour += 1
                dailyHP.append(last7daysHP[clef])
            status_counts['dailyweek_HP'] = [("{:.3f}".format(0.001 * day_HP)) for day_HP in dailyHP]

            status_counts["halfhourly"] = []
            status_counts["offpeak_hours"] = _myDataEnedis.getYesterdayHC() * 0.001
            status_counts["peak_hours"] = _myDataEnedis.getYesterdayHP() * 0.001
            if ((_myDataEnedis.getYesterdayHC() + _myDataEnedis.getYesterdayHP()) != 0):
                status_counts["peak_offpeak_percent"] = (_myDataEnedis.getYesterdayHP() * 100) / \
                        ( _myDataEnedis.getYesterdayHC() + _myDataEnedis.getYesterdayHP())
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
            status_counts["yesterday_HC_cost"] + status_counts["yesterday_HP_cost"]
            status_counts['current_week'] = _myDataEnedis.getCurrentWeek() * 0.001
            status_counts['last_month'] = _myDataEnedis.getLastMonth() * 0.001
            status_counts['current_month'] = _myDataEnedis.getCurrentMonth() * 0.001
            status_counts['last_year'] = _myDataEnedis.getLastYear() * 0.001
            status_counts['current_year'] = _myDataEnedis.getCurrentYear() * 0.001
            status_counts['errorLastCall'] = _myDataEnedis.getErrorLastCall()
            if ((_myDataEnedis.getLastMonthLastYear() != None) and
                    (_myDataEnedis.getLastMonthLastYear() != 0) and
                    (_myDataEnedis.getLastMonth() != None)):
                status_counts["monthly_evolution"] = \
                    ((_myDataEnedis.getLastMonth() - _myDataEnedis.getLastMonthLastYear())
                     / _myDataEnedis.getLastMonthLastYear()) * 100
            else:
                status_counts["monthly_evolution"] = 0
            status_counts["subscribed_power"] = _myDataEnedis.getsubscribed_power()
            status_counts["offpeak_hours_information"] = _myDataEnedis.getoffpeak_hours()
            # status_counts['yesterday'] = ""

        except:
            status_counts['errorLastCall'] = _myDataEnedis.getErrorLastCall()
            _LOGGER.warning( "errorLastCall : %s " %( _myDataEnedis.getErrorLastCall() ))

    return status_counts

def logSensorState( status_counts ):
    for x in status_counts.keys():
        print(" %s : %s" %( x, status_counts[x]))