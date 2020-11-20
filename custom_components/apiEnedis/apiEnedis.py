import requests
import datetime, time
import json
import logging

__nameMyEnedis__ = "apiEnedis"
class apiEnedis:
    def __init__(self, token, PDL_ID, delai = 3600, heuresCreuses = None, \
                 heuresCreusesCost=0, heuresPleinesCost=0, log = None):
        self._token = token
        self._PDL_ID = PDL_ID
        self._lastMonth = None
        self._lastYear = None
        self._currentMonth = None
        self._currentYear = None
        self._lastWeek = None
        self._last7Days = None
        self._lastMonthLastYear = None
        self._currentWeek = None
        self._yesterday = None
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall = False
        self._errorLastCall = None
        self._lastAnswer = None
        self._delai = delai
        self._heuresCreuses = heuresCreuses
        self._heuresCreusesCost = heuresCreusesCost
        self._heuresPleinesCost = heuresPleinesCost
        self._HC = 0
        self._HP = 0
        if ( log == None ):
            self._log = logging.getLogger(__nameMyEnedis__)
            self._log.setLevel(logging.DEBUG)
        else:
            self._log = log
            self._log.setLevel(logging.DEBUG)
        pass

    def myLog(self, message):
        self._log.warning(message)

    def post_and_get_json(self, url, params=None, data=None, headers=None):
        try:
            import logging
            import json

            response = requests.post(url, params=params, data=json.dumps(data), headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            return response.json()

    def setLastAnswsr(self, lastanswer ):
        self._lastAnswer = lastanswer
    def getLastAnswer(self):
        return self._lastAnswer

    def getDataPeriod(self, deb, fin ):
        self.myLog("--get dataPeriod : %s => %s --" %( deb, fin ))
        payload = {
            'type': 'daily_consumption',
            'usage_point_id': self._PDL_ID,
            'start': '%s' %(deb),
            'end': '%s' %(fin),
        }
        headers = {
            'Authorization': self._token,
            'Content-Type': "application/json",
        }
        dataAnswer = self.post_and_get_json("https://enedisgateway.tech/api", data=payload, headers=headers)
        self.setLastAnswsr( dataAnswer )
        return dataAnswer

    def getDataPeriodCLC(self, deb, fin ):
        payload = {
            'type': 'consumption_load_curve',
            'usage_point_id': self._PDL_ID,
            'start': '%s' %(deb),
            'end': '%s' %(fin),
        }
        headers = {
            'Authorization': self._token,
            'Content-Type': "application/json",
        }
        dataAnswer = self.post_and_get_json("https://enedisgateway.tech/api", data=payload, headers=headers)
        self.setLastAnswsr( dataAnswer )
        return dataAnswer

    def CallgetYesterday(self):
        hier = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriod( hier, cejour )

    def CallgetDataYesterdayHCHP(self):
        hier = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriodCLC( hier, cejour )

    def CallgetCurrentWeek(self):
        import datetime
        today = datetime.date.today()
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        firstdateofweek = (datetime.date.today()-datetime.timedelta(days=datetime.datetime.today().weekday() % 7)).strftime("%Y-%m-%d")
        if ( cejour == firstdateofweek ):
            return 0 # cas lundi = premier jour de la semaine et donc rien de dispo
        else:
            return self.getDataPeriod( firstdateofweek, cejour)

    def CallgetLast7Days(self):
        import datetime
        today = datetime.date.today()
        start_date = today - datetime.timedelta(7)
        end_date = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriod( start_date, end_date)

    def CallgetLastWeek(self):
        import datetime
        today = datetime.date.today()
        start_date = today + datetime.timedelta(-today.weekday(), weeks=-1)
        end_date = today + datetime.timedelta(-today.weekday())
        return self.getDataPeriod( start_date, end_date)

    def CallgetLastMonth(self):
        import datetime
        today = datetime.date.today()
        first = today.replace(day=1)
        lastMonth = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonth.strftime("%Y-%m-01")
        debCurrentMonth = first.strftime("%Y-%m-01")
        return self.getDataPeriod( debPreviousMonth, debCurrentMonth )

    def CallgetLastMonthLastYear(self):
        import datetime
        today = datetime.date.today()
        first = today.replace(day=1, year=today.year-1)
        lastMonthLastYear = first - datetime.timedelta(days=1)
        debPreviousMonth = lastMonthLastYear.strftime("%Y-%m-01")
        debCurrentMonth = first.strftime("%Y-%m-01")
        return self.getDataPeriod( debPreviousMonth, debCurrentMonth )


    def CallgetLastYear(self):
        import datetime
        today = datetime.date.today()
        first = today.replace(day=1, month=1)
        lastYear = first - datetime.timedelta(days=1)
        debPreviousYear = lastYear.strftime("%Y-01-01")
        debCurrentYear = today.strftime("%Y-01-01")
        return self.getDataPeriod( debPreviousYear, debCurrentYear )

    def CallgetCurrentMonth(self):
        import datetime
        today = datetime.date.today()
        debCurrentMonth = today.strftime("%Y-%m-01")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        if ( debCurrentMonth != cejour ):
            return self.getDataPeriod( debCurrentMonth, cejour)
        else:
            return 0

    def CallgetCurrentYear(self):
        import datetime
        today = datetime.date.today()
        debCurrentMonth = today.strftime("%Y-01-01")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriod( debCurrentMonth, cejour)

    def analyseValueAndAdd(self, data):
        if ( data == None ): #pas de valeur
            raise Exception( 'call' , None )
        else:
            tot = 0
            for x in data["meter_reading"]["interval_reading"]:
                tot += int(x["value"])
            return tot

    def analyseValueAndMadeDico(self, data):
        dicoLast7days = []
        if ( data == None ): #pas de valeur
            raise Exception( 'call' , None )
        else:
            niemejour = 0
            for x in reversed(data["meter_reading"]["interval_reading"]):
                niemejour += 1
                days = {}
                days[ 'date'] = x[ 'date']
                days[ 'niemejour'] = niemejour
                days[ 'value'] = int( x[ 'value'] )
                dicoLast7days.append(days)
        return dicoLast7days

    def analyseValue(self, data):
        if ( data == None ): #pas de valeur
            return None
        else:
            return int(data["meter_reading"]["interval_reading"][0]["value"])

    def getYesterday(self):
        return self._yesterday

    def updateYesterday(self, data=None):
        self.myLog("--updateYesterday --")
        if ( data == None ): data = self.CallgetYesterday()
        self.myLog("updateYesterday : data %s" %(data))
        self.checkData( data )
        self._yesterday = self.analyseValue( data )
    def getYesterdayHP(self):
        return self._HP
    def getYesterdayHC(self):
        return self._HC
    def getHCCost(self, val):
        return val*self._heuresCreusesCost*0.5 # car à l'heure et non à la demi-heure
    def getHPCost(self, val):
        return val*self._heuresPleinesCost*0.5 # car à l'heure et non à la demi-heure
    def createHCHP(self, data):
        self._HP = 0
        self._HC = 0
        for x in data["meter_reading"]["interval_reading"]:
            heure = x["date"][11:16]
            heurePleine = True
            for heureCreuse in self._heuresCreuses:
                try: # gestion du 00:00 en heure de fin de creneau
                    if ( heure == {"24:00":"00:00"}[heureCreuse[1]]):
                        heurePleine = False
                except:
                    pass
                if (heureCreuse[0] < heure) and (heure <= heureCreuse[1]):
                    heurePleine = False
            #print ( heure, "==>", heurePleine)
            if ( heurePleine):
                self._HP += int(x["value"])
                #print( heure, heurePleine, x[ "value" ], self._HP)
            else:
                self._HC += int(x["value"])
                #print( heure, heurePleine, x[ "value" ], self._HC)
        #print(self._HC)
        #print(self._HP)

    def updateDataYesterdayHCHP(self, data=None):
        self.myLog("--updateDataHCHP --")
        if (data == None): data = self.CallgetDataYesterdayHCHP()
        self.myLog("updateDataHCHP : data %s" % (data))
        self.checkData(data)
        self.createHCHP(data)

    def checkDataPeriod(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            raise Exception( 'call' , "error", dataAnswer['enedis_return']["error"] )

    def checkData(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            raise Exception( 'call' , "error", dataAnswer['enedis_return']["error"] )

    def getLastMonth(self):
        return self._lastMonth
    def updateLastMonth(self, data=None):
        self.myLog("--updateLastMonth --")
        if ( data == None ): data = self.CallgetLastMonth()
        self.myLog("updateLastMonth : data %s" %(data))
        self.checkDataPeriod(data)
        self._lastMonth = self.analyseValueAndAdd( data )

    def getLastMonthLastYear(self):
        return self._lastMonthLastYear
    def updateLastMonthLastYear(self, data=None):
        self.myLog("--updateLastMonthLastYear --")
        if ( data == None ): data = self.CallgetLastMonthLastYear()
        self.myLog("updateLastMonthLastYear : data %s" %(data))
        self.checkDataPeriod(data)
        self._lastMonthLastYear = self.analyseValueAndAdd( data )

    def getLastWeek(self):
        return self._lastWeek
    def updateLastWeek(self, data=None):
        self.myLog("--updateLastWeek --")
        if ( data == None ): data = self.CallgetLastWeek()
        self.myLog("updateLastWeek : data %s" %(data))
        self.checkDataPeriod(data)
        self._lastWeek = self.analyseValueAndAdd( data )

    def getLast7Days(self):
        return self._last7Days
    def updateLast7Days(self, data=None):
        self.myLog("--updateLast7Days --")
        if ( data == None ): data = self.CallgetLast7Days()
        self.myLog("updateLast7Days : data %s" %(data))
        self.checkDataPeriod(data)
        # construction d'un dico utile ;)
        self._last7Days = self.analyseValueAndMadeDico( data )

    def getCurrentWeek(self):
        return self._currentWeek
    def updateCurrentWeek(self, data=None):
        self.myLog("--updateCurrentWeek --")
        if ( data == None ): data = self.CallgetCurrentWeek()
        self.myLog("updateCurrentWeek : data %s" %(data))
        if ( data != 0 ):
            self.checkDataPeriod(data)
            self._currentWeek = self.analyseValueAndAdd( data )
        else:
            self._currentWeek = data

    def getCurrentMonth(self):
        return self._currentMonth
    def updateCurrentMonth(self, data=None):
        self.myLog("--updateCurrentMonth --")
        if ( data == None ): data = self.CallgetCurrentMonth()
        self.myLog("updateCurrentMonth : data %s" %(data))
        if ( data != 0 ):
            self.checkDataPeriod(data)
            self._currentMonth = self.analyseValueAndAdd( data )
        else:
            self._currentMonth = data
    def getLastYear(self):
        return self._lastYear
    def updateLastYear(self, data=None):
        self.myLog("--updateLastYear --")
        if ( data == None ): data = self.CallgetLastYear()
        self.myLog("updateLastYear : data %s" %(data))
        self.checkDataPeriod(data)
        self._lastYear =  self.analyseValueAndAdd( data )

    def getCurrentYear(self):
        return self._currentYear
    def updateCurrentYear(self, data=None):
        self.myLog("--updateCurrentYear --")
        if ( data == None ): data = self.CallgetCurrentYear()
        self.myLog("updateCurrentYear : data %s" %(data))
        self.checkDataPeriod(data)
        self._currentYear = self.analyseValueAndAdd( data )

    def getLastUpdate(self):
        return self._lastUpdate
    def updateLastUpdate(self):
        self._lastUpdate = datetime.datetime.now()

    def getTimeLastCall(self):
        return self._timeLastUpdate
    def updateTimeLastCall(self):
        self._timeLastUpdate = datetime.datetime.now()

    def getStatusLastCall(self):
        return self._statusLastCall
    def updateStatusLastCall(self, status):
        self._statusLastCall = status

    def getErrorLastCall(self):
        return self._errorLastCall
    def updateErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def getDelai(self):
        return self._delai
    def getDelaiIsGood(self):
        ecartOk = ( datetime.datetime.now() - self.getTimeLastCall()).seconds > self.getDelai()
        return ecartOk

    def update(self):
        if (( self.getTimeLastCall() == None ) or
            ( self.getStatusLastCall() == False) or
            ( self.getDelaiIsGood() )):
            print("on doit updater")
            try:
                self.updateYesterday()
                try:
                    self.updateCurrentWeek()
                    self.updateLastWeek()
                    self.updateLast7Days()
                    self.updateCurrentMonth()
                    self.updateLastMonth()
                    self.updateCurrentYear()
                    self.updateDataYesterdayHCHP()
                    self.updateLastYear()
                    self.updateLastMonthLastYear()
                    self.updateTimeLastCall()
                    self.updateStatusLastCall( True )
                except Exception as inst:
                    if ( inst.args[:2] == ("call", "error")): # gestion que c'est pas une erreur de contrat trop recent ?
                        print("Erreur call ERROR ", inst.args)
                        # Erreur lors du call...
                        self.updateTimeLastCall()
                        self.updateStatusLastCall( True )
                        self.updateErrorLastCall( "%s"%(self.getLastAnswer()))
            except Exception as inst:
                if ( inst.args == ("call", None)):
                    print("Erreur call")
                    # Erreur lors du call...
                    # Erreur lors du call...
                    self.updateTimeLastCall()
                    self.updateStatusLastCall( False )
                    self.updateErrorLastCall( "%s"%(self.getLastAnswer()))
                else:
                    print("Erreur inconnue call ERROR ", inst)
                    print("Erreur last answer", inst)

        else:
            print("pas d'update trop tot !!!")
        self.updateLastUpdate()

def main():
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../../../myCredential/security.txt")
    token = mon_conteneur['ENEDIS']['TOKEN']
    PDL_ID = mon_conteneur['ENEDIS']['CODE']


    heureCreusesCh = "[['00:00','05:00'], ['22:00', '24:00']]"
    myDataEnedis = apiEnedis( token=token, PDL_ID=PDL_ID, delai = 10, \
        heuresCreuses=eval(heureCreusesCh),
        heuresCreusesCost=0.20,
        heuresPleinesCost=1.30)
    #myDataEnedis = apiEnedis( token=token, PDL_ID=PDL_ID, delai = 10, \
    #    heuresCreuses=[],
    #    heuresCreusesCost=0.20,
    #    heuresPleinesCost=1.30) # on fait un update 10 secondes après le dernier ok

    " Gestion du cas ou la requete yesrday ne donne rien"
    #data = {'error': 'result_400', 'enedis_return': {'error': 'Invalid_request', 'error_description': 'Start date should be before end date.', 'error_uri': 'https://bluecoder.enedis.fr/api-doc/consulter-souscrire'}}
    #myDataEnedis.updateYesterday( data )
    #data = {'error': 'result_404', 'enedis_return': {'error': 'no_data_found', 'error_description': 'no measure found for this usage point', 'error_uri': 'https://bluecoder.enedis.fr/api-doc/consulter-souscrire'}}
    #myDataEnedis.updateYesterday(data)
    #data = {"meter_reading":{"usage_point_id":"25869464529695","start":"2020-11-12","end":"2020-11-13","quality":"BRUT","interval_reading":[{"value":"1142","date":"2020-11-12 00:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1854","date":"2020-11-12 01:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"3366","date":"2020-11-12 01:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"4224","date":"2020-11-12 02:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"4132","date":"2020-11-12 02:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"3898","date":"2020-11-12 03:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"2852","date":"2020-11-12 03:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"826","date":"2020-11-12 04:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"986","date":"2020-11-12 04:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1722","date":"2020-11-12 05:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1742","date":"2020-11-12 05:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"716","date":"2020-11-12 06:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"756","date":"2020-11-12 06:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1502","date":"2020-11-12 07:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1314","date":"2020-11-12 07:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"792","date":"2020-11-12 08:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"668","date":"2020-11-12 08:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"670","date":"2020-11-12 09:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"678","date":"2020-11-12 09:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"702","date":"2020-11-12 10:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"724","date":"2020-11-12 10:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"4394","date":"2020-11-12 11:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"4034","date":"2020-11-12 11:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1830","date":"2020-11-12 12:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"682","date":"2020-11-12 12:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"846","date":"2020-11-12 13:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"860","date":"2020-11-12 13:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"906","date":"2020-11-12 14:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1944","date":"2020-11-12 14:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"2218","date":"2020-11-12 15:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1090","date":"2020-11-12 15:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"822","date":"2020-11-12 16:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"832","date":"2020-11-12 16:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"912","date":"2020-11-12 17:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"874","date":"2020-11-12 17:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1760","date":"2020-11-12 18:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"3484","date":"2020-11-12 18:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"1892","date":"2020-11-12 19:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"856","date":"2020-11-12 19:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"922","date":"2020-11-12 20:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1598","date":"2020-11-12 20:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"902","date":"2020-11-12 21:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"894","date":"2020-11-12 21:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"916","date":"2020-11-12 22:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"2096","date":"2020-11-12 22:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"2128","date":"2020-11-12 23:00:00","interval_length":"PT30M","measure_type":"B"},{"value":"1376","date":"2020-11-12 23:30:00","interval_length":"PT30M","measure_type":"B"},{"value":"866","date":"2020-11-13 00:00:00","interval_length":"PT30M","measure_type":"B"}],"reading_type":{"unit":"W","measurement_kind":"power","aggregate":"average"}}}
    response = myDataEnedis.updateDataYesterdayHCHP()
    #print(response)
    print(myDataEnedis.getYesterdayHC())
    print(myDataEnedis.getYesterdayHP())
    print(myDataEnedis.getHCCost(myDataEnedis.getYesterdayHC()))
    print(myDataEnedis.getHPCost(myDataEnedis.getYesterdayHP()))
    #print(1/0)
    #myDataEnedis.updateCurrentWeek()
    #print(1/0)
    #myDataEnedis.updateCurrentMonth()
    #myDataEnedis.update()
    print( myDataEnedis.getYesterday(),
           myDataEnedis.getCurrentMonth(),
           myDataEnedis.getLastMonth(),
           myDataEnedis.getLastMonthLastYear(),
           myDataEnedis.getCurrentWeek(),
           myDataEnedis.getLastWeek(),
           myDataEnedis.getLast7Days(),
           myDataEnedis.getCurrentYear(),
           myDataEnedis.getLastYear() )
    print( myDataEnedis.getTimeLastCall(), myDataEnedis.getLastUpdate(), myDataEnedis.getStatusLastCall())
    print( myDataEnedis.getErrorLastCall())
    print("HC/HP")
    print( myDataEnedis.getYesterdayHC())
    print( myDataEnedis.getYesterdayHP())
    #last7days = myDataEnedis.getLast7Days()
    #for day in last7days:
    #    print('day_%s' % (day["niemejour"]), day["value"] )
#
if __name__ == '__main__':
    main()

""" get all update and charge l'instance et utilisation avec get after ....."""