import requests
import datetime, time
import json
import logging

__nameMyEnedis__ = "apiEnedis"
class apiEnedis:
    def __init__(self, token, PDL_ID, delai = 3600, heuresCreuses = None, \
                 heuresCreusesCost=0, heuresPleinesCost=0, log = None):
        self._serverName = "https://enedisgateway.tech/api"
        self._token = token
        self._PDL_ID = PDL_ID
        self._lastMonth = None
        self._lastYear = None
        self._currentMonth = None
        self._currentYear = None
        self._lastWeek = None
        self._last7Days = []
        self._lastMonthLastYear = None
        self._currentWeek = None
        self._yesterday = None
        self._productionYesterday = None
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall = True
        self._errorLastCall = None
        self._lastAnswer = None
        self._errorLastMethodCall = None
        self._errorLastMethodCallError = None
        self._delai = delai
        self._heuresCreuses = heuresCreuses
        self._heuresCreusesCost = heuresCreusesCost
        self._heuresPleinesCost = heuresPleinesCost
        self._contract = None #{'subscribed_power':"", 'offpeak_hours':""}
        self._HC, self._HP = 0, 0
        self._interval_length = 1
        self._updateRealise = False
        self._niemeAppel = 0

        self._joursHC={}
        self._joursHP={}
        if ( log == None ):
            self._log = logging.getLogger(__nameMyEnedis__)
            self._log.setLevel(logging.DEBUG)
            #self._log.setLevel(logging.WARNING)
        else:
            self._log = log
            self._log.setLevel(logging.DEBUG)
        pass

    def myLog(self, message):
        #self._log.info(message)
        #self._log.warning(message)
        pass

    def myLogWarning(self, message):
        self._log.warning(message)

    def setUpdateRealise(self, value):
        self._updateRealise = value
    def getUpdateRealise(self):
        return self._updateRealise
    def get_PDL_ID(self):
        return self._PDL_ID
    def post_and_get_json(self, url, params=None, data=None, headers=None):
        try:
            import logging
            import json

            session = requests.Session()
            response = session.post(url, params=params, data=json.dumps(data), headers=headers)
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
        dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
        self.setLastAnswsr( dataAnswer )
        return dataAnswer

    def getDataProductionPeriod(self, deb, fin ):
        self.myLog("--get ProductionPeriod : %s => %s --" %( deb, fin ))
        payload = {
            'type': 'daily_production',
            'usage_point_id': self._PDL_ID,
            'start': '%s' %(deb),
            'end': '%s' %(fin),
        }
        headers = {
            'Authorization': self._token,
            'Content-Type': "application/json",
        }
        dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
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
        dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
        self.setLastAnswsr( dataAnswer )
        return dataAnswer

    def getDataContract(self, ):
        payload = {
            'type': 'contracts',
            'usage_point_id': self._PDL_ID,
        }
        headers = {
            'Authorization': self._token,
            'Content-Type': "application/json",
        }
        dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
        self.setLastAnswsr( dataAnswer )
        return dataAnswer

    def CallgetDataContract(self):
        return self.getDataContract()

    def CallgetYesterday(self):
        hier = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriod( hier, cejour )

    def CallgetProductionYesterday(self):
        hier = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataProductionPeriod( hier, cejour )

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

    def CallgetLast7DaysDetails(self):
        import datetime
        today = datetime.date.today()
        start_date = today - datetime.timedelta(7)
        end_date = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriodCLC( start_date, end_date)

    def CallgetCurrentMonthDetails(self):
        import datetime
        today = datetime.date.today()
        debCurrentMonth = today.strftime("%Y-%m-01")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        if (debCurrentMonth != cejour):
            return self.getDataPeriodCLC(debCurrentMonth, cejour)
        else:
            return 0

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
    def analyseValueContract(self, data):
        if ( data == None ): #pas de valeur
            return None
        else:
            contract = None
            for x in data['customer']['usage_points']:
                if ( str(x["usage_point"]['usage_point_id']) == self._PDL_ID):
                    contract = {}
                    contract['contracts'] = x["contracts"]
                    if ( "subscribed_power" in x["contracts"]):
                        contract['subscribed_power']= x["contracts"]["subscribed_power"]
                        contract["mode_PDL"] = "consommation"
                    else:
                        contract["mode_PDL"] = "production"
                        contract['subscribed_power']= "???"
                    if ( "offpeak_hours" in x["contracts"]):
                        contract['offpeak_hours']= x["contracts"]["offpeak_hours"]
                    else:
                        contract['offpeak_hours']= None
            return contract

    def getContract(self):
        return self._contract
    def getsubscribed_power(self):
        return self._contract['subscribed_power']
    def getoffpeak_hours(self):
        return self._contract['offpeak_hours']
    def getTypePDL(self):
        return self._contract["mode_PDL"]
    def isConsommation(self):
        return self._contract["mode_PDL"] == "consommation"
    def isProduction(self):
        return self._contract["mode_PDL"] == "production"
    def getcleanoffpeak_hours(self, offpeak=None):
        if ( offpeak == None ): offpeak = self._contract['offpeak_hours']
        if ( offpeak != None ):
            offpeakClean1 = offpeak.split("(")[1].replace(")","").replace("H",":").replace(";","-").split("-")
            opcnew = []
            deb = ""
            fin = ""
            lastopc = ""
            for opc in offpeakClean1:
                opc = opc.rjust(5).replace(" ", "0")
                if ( lastopc != "" ):
                    fin = opc
                    if ( lastopc> opc):
                        fin = "23:59"
                        opcnew.append([deb, fin])
                        deb = "00:00"
                        fin = opc
                    opcnew.append([deb, fin])
                    deb = opc
                else:
                    deb = opc
                lastopc = opc
        else:
            opcnew = []
        return opcnew

    def updateContract(self, data=None):
        self.updateLastMethodCall("updateContract")
        self.myLog("--updateContract --")
        if ( data == None ): data = self.CallgetDataContract()
        self.myLog("updateContract : data %s" %(data))
        self.checkDataContract( data )
        self._contract = self.analyseValueContract( data )

    def updateHCHP(self, heuresCreuses=None):
        if ( heuresCreuses != None ): self._heuresCreuses = heuresCreuses
        else:
            self._heuresCreuses = self.getcleanoffpeak_hours()

    def getYesterday(self):
        return self._yesterday

    def updateYesterday(self, data=None):
        self.updateLastMethodCall("updateYesterday")
        self.myLog("--updateYesterday --")
        if ( data == None ): data = self.CallgetYesterday()
        self.myLog("updateYesterday : data %s" %(data))
        if ( self.checkData( data )):
            self._yesterday = self.analyseValue( data )
        else:
            self._yesterday = 0
    def getProductionYesterday(self):
        return self._productionYesterday

    def updateProductionYesterday(self, data=None):
        self.updateLastMethodCall("updateProductionYesterday")
        self.myLog("--updateProductionYesterday --")
        if ( data == None ): data = self.CallgetProductionYesterday()
        self.myLog("updateProductionYesterday : data %s" %(data))
        self.checkData( data )
        self._productionYesterday = self.analyseValue( data )
    def getYesterdayHP(self):
        return self._HP
    def getYesterdayHC(self):
        return self._HC
    def get7DaysHP(self):
        return self._joursHP
    def get7DaysHC(self):
        return self._joursHC
    def getHCCost(self, val):
        return val*self._heuresCreusesCost # car à l'heure et non à la demi-heure
    def getHPCost(self, val):
        return val*self._heuresPleinesCost # car à l'heure et non à la demi-heure

    def _getHCHPfromHour(self, heure):
        heurePleine = True
        for heureCreuse in self._heuresCreuses:
            try:  # gestion du 00:00 en heure de fin de creneau
                if (heure == {"24:00": "00:00"}[heureCreuse[1]]):
                    heurePleine = False
            except:
                pass
            if (heureCreuse[0] < heure) and (heure <= heureCreuse[1]):
                heurePleine = False
        return heurePleine

    def createMultiDaysHCHP(self, data):
        joursHC={}
        joursHP={}
        dateDuJour = (datetime.date.today()).strftime("%Y-%m-%d")
        for x in data["meter_reading"]["interval_reading"]:
            self._interval_length = x["interval_length"]
            date = x["date"][:10]
            heure = x["date"][11:16]
            if ( heure == "00:00" ): # alors sur la veille, var c'est la fin de la tranche du jour precedent
                date = (datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(1) ).strftime("%Y-%m-%d")

            #if ( date == dateDuJour ):
            #    print("ici", x["date"], x["value"])
            #    pass
            #else:
            if(1):
                if date not in joursHC:joursHC[date] = 0
                if date not in joursHP:joursHP[date] = 0
                heurePleine = self._getHCHPfromHour( heure )
                if (heurePleine):
                    joursHP[date] += int(x["value"]) * self.getCoeffIntervalLength() # car c'est en heure
                else:
                    joursHC[date] +=int(x["value"]) * self.getCoeffIntervalLength() # car c'est pas en heure

                # if ( date == "2020-12-06" ):
                #     print("ici", x["date"], heure, " ", heurePleine, ", ", x[ "value" ], \
                #           self._joursHP[date], self._joursHC[date], self._joursHP[date] + self._joursHC[date])

        return joursHC, joursHP
        #print(self._joursHC)
        #print(self._joursHP)

    def getIntervalLength(self):
        return self._interval_length
    def getCoeffIntervalLength(self):
        interval = self.getIntervalLength()
        coeff = 1
        if ( interval == "PT10M" ) : coeff = 1 * 10 / 60
        if ( interval == "PT20M" ) : coeff = 1 * 20 / 60
        if ( interval == "PT30M" ) : coeff = 1 * 30 / 60
        return coeff

    def createHCHP(self, data):
        self._HP = 0
        self._HC = 0
        for x in data["meter_reading"]["interval_reading"]:
            self._interval_length = x["interval_length"]
            heure = x["date"][11:16]
            heurePleine = self._getHCHPfromHour( heure )
            if ( heurePleine):
                self._HP += int(x["value"]) * self.getCoeffIntervalLength()# car par transhce de 30 minutes
                #print( heure, heurePleine, x[ "value" ], self._HP)
            else:
                self._HC += int(x["value"]) * self.getCoeffIntervalLength()# car par transhce de 30 minutes
            #print( heure, " ", heurePleine, ", ", x[ "value" ], self._HC, self._HP, self._HC + self._HP)
        #print(self._HC)
        #print(self._HP)

    def updateDataYesterdayHCHP(self, data=None):
        self.updateLastMethodCall("updateDataYesterdayHCHP")
        self.myLog("--updateDataYesterdayHCHP --")
        if (data == None): data = self.CallgetDataYesterdayHCHP()
        self.myLog("updateDataYesterdayHCHP : data %s" % (data))
        self.checkData(data)
        self.createHCHP(data)

    def checkDataPeriod(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            if ( dataAnswer['enedis_return']["error"] == "ADAM-ERR0123" ) :
                return False
            elif ( dataAnswer['enedis_return']["error"] == "no_data_found" ) :
                return False
            else:
                raise Exception( 'call' , "error", dataAnswer['enedis_return']["error"] )
        return True

    def checkData(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            if ( isinstance(dataAnswer['enedis_return'], str)):
                dataAnswer['enedis_return'] = json.loads(dataAnswer['enedis_return'])
            if ( dataAnswer['enedis_return']["error"] == "ADAM-DC-0008" ):
                #No consent can be found for this customer and this usage point
                return False
            else:
                raise Exception( 'call' , "error", dataAnswer['enedis_return']["error"] )
        return True

    def checkDataContract(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            self.myLogWarning( "** %s" %(dataAnswer["error"]))
            raise Exception( 'call' , "error", dataAnswer["error"] )

    def getLastMonth(self):
        return self._lastMonth
    def updateLastMonth(self, data=None):
        self.updateLastMethodCall("updateLastMonth")
        self.myLog("--updateLastMonth --")
        if ( data == None ): data = self.CallgetLastMonth()
        self.myLog("updateLastMonth : data %s" %(data))
        if ( self.checkDataPeriod(data)):
            self._lastMonth = self.analyseValueAndAdd( data )
        else:
            self._lastMonth = 0

    def getLastMonthLastYear(self):
        return self._lastMonthLastYear
    def updateLastMonthLastYear(self, data=None):
        self.updateLastMethodCall("updateLastMonthLastYear")
        self.myLog("--updateLastMonthLastYear --")
        if ( data == None ): data = self.CallgetLastMonthLastYear()
        self.myLog("updateLastMonthLastYear : data %s" %(data))
        if ( self.checkDataPeriod(data)):
            self._lastMonthLastYear = self.analyseValueAndAdd( data )
        else:
            self._lastMonthLastYear = 0

    def getLastWeek(self):
        return self._lastWeek
    def updateLastWeek(self, data=None):
        self.updateLastMethodCall("updateLastWeek")
        self.myLog("--updateLastWeek --")
        if ( data == None ): data = self.CallgetLastWeek()
        self.myLog("updateLastWeek : data %s" %(data))
        self.checkDataPeriod(data)
        self._lastWeek = self.analyseValueAndAdd( data )

    def getLast7Days(self):
        return self._last7Days
    def updateLast7Days(self, data=None):
        self.updateLastMethodCall("updateLast7Days")
        self.myLog("--updateLast7Days --")
        if ( data == None ): data = self.CallgetLast7Days()
        self.myLog("updateLast7Days : data %s" %(data))
        self.checkDataPeriod(data)
        # construction d'un dico utile ;)
        self._last7Days = self.analyseValueAndMadeDico( data )

    def getLast7DaysDetails(self):
        return self._last7DaysDetails
    def updateLast7DaysDetails(self, data=None):
        self.updateLastMethodCall("updateLast7DaysDetails")
        self.myLog("--updateLast7DaysDetails --")
        if ( data == None ): data = self.CallgetLast7DaysDetails()
        self.myLog("updateLast7DaysDetails : data %s" %(data))
        self.checkDataPeriod(data)
        # construction d'un dico utile ;)
        self._joursHC, self._joursHP =  self.createMultiDaysHCHP(data)

    def getCurrentWeek(self):
        return self._currentWeek
    def updateCurrentWeek(self, data=None):
        self.updateLastMethodCall("updateCurrentWeek")
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
        self.updateLastMethodCall("updateCurrentMonth")
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
        self.updateLastMethodCall("updateLastYear")
        self.myLog("--updateLastYear --")
        if ( data == None ): data = self.CallgetLastYear()
        self.myLog("updateLastYear : data %s" %(data))
        if ( self.checkDataPeriod(data)):
            self._lastYear =  self.analyseValueAndAdd( data )
        else: # pas de donnée disponible
            self._lastYear = 0

    def getCurrentYear(self):
        return self._currentYear
    def updateCurrentYear(self, data=None):
        self.updateLastMethodCall("updateCurrentYear")
        self.myLog("--updateCurrentYear --")
        if ( data == None ): data = self.CallgetCurrentYear()
        self.myLog("updateCurrentYear : data %s" %(data))
        if ( self.checkDataPeriod(data)):
            self._currentYear = self.analyseValueAndAdd( data )
        else:
            self._currentYear = 0

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
    def getLastMethodCall(self):
        return self._errorLastMethodCall
    def getLastMethodCallError(self):
        return self._errorLastMethodCallError
    def updateLastMethodCall(self, methodName):
        self._errorLastMethodCall = methodName
        if ( self._errorLastMethodCallError == self._errorLastMethodCall ):
            self._errorLastMethodCallError = ""
            self.updateStatusLastCall(True) # pour la prochaine reprenne normalement car tout est conforme
    def updateLastMethodCallError(self, methodName):
        self._errorLastMethodCallError = methodName
    def updateErrorLastCall(self, errorMessage):
        self._errorLastCall = errorMessage

    def getDelai(self):
        return self._delai
    def getDelaiIsGood(self):
        self.myLogWarning("TimeLastCall : %s" %(self.getTimeLastCall()))
        ecartOk = ( datetime.datetime.now() - self.getTimeLastCall()).seconds > self.getDelai()
        return ecartOk

    def update(self):
        if (( self.getTimeLastCall() == None ) or
            ( self.getStatusLastCall() == False) or
            ( self.getDelaiIsGood() )):
            try:
                self.myLogWarning( "myEnedis ...%s update lancé, status precedent : %s, lastCall :%s" \
                                   % (self.get_PDL_ID(), self.getStatusLastCall(), self.getLastMethodCallError()))
                self.updateErrorLastCall( "")
                self.updateLastMethodCall("")
                self.setUpdateRealise( True )
                if ( self.isConsommation()):
                    self._niemeAppel += 1
                    if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateYesterday"):

                        """if (self.get_PDL_ID() == "xxx") and \
                                ( self._niemeAppel >= 2 ) and ( self._niemeAppel < 4 ):
                            self.myLogWarning("*** TEST CRASH CONTRACT xxxx *** %s" %(self._niemeAppel))
                            print(1/0)  # on crash pour voir la reprise ;) """
                        self.updateYesterday()
                    try:
                        if( self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentWeek"):
                            self.updateCurrentWeek()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastWeek"):
                            self.updateLastWeek()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLast7Days"):
                            self.updateLast7Days()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentMonth"):
                            self.updateCurrentMonth()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastMonth"):
                            self.updateLastMonth()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateCurrentYear"):
                            self.updateCurrentYear()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateDataYesterdayHCHP"):
                            try:
                                self.updateDataYesterdayHCHP()
                            except Exception as inst:
                                if ( inst.args[:3] == ('call', 'error', 'no_data_found')): # gestion que c'est pas une erreur de contrat trop recent ?
                                    # si le service ne repond pas, l'erreur pas grave, c'est que pas encore remonté
                                    self.updateErrorLastCall( "%s"%("no yesterday data"))
                                    pass
                                else:
                                    raise Exception(inst)

                        # if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateDataYesterdayHCHP"):
                        #     self.updateDataYesterdayHCHP()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastYear"):
                            self.updateLastYear()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLastMonthLastYear"):
                            self.updateLastMonthLastYear()
                        if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateLast7DaysDetails"):
                            self.updateLast7DaysDetails()
                        self.updateTimeLastCall()
                        self.updateStatusLastCall( True )
                        self.myLogWarning("mise à jour effectuee")
                    except Exception as inst:
                        if ( inst.args[:2] == ("call", "error")): # gestion que c'est pas une erreur de contrat trop recent ?
                            self.myLogWarning("%s - Erreur call ERROR %s" %(self.get_PDL_ID(), inst))
                            # Erreur lors du call...
                            self.updateTimeLastCall()
                            self.updateStatusLastCall( False )
                            self.updateErrorLastCall( "%s"%(self.getLastAnswer()))
                            self.myLogWarning( "%s - last call : %s" %(self.get_PDL_ID(), self.getLastMethodCall()))
                elif ( self.isProduction()):
                    if (self.getStatusLastCall() or self.getLastMethodCallError() == "updateProductionYesterday"):
                        self.updateProductionYesterday()
                    self.updateTimeLastCall()
                    self.updateStatusLastCall(True)

            except Exception as inst:
                if ( inst.args == ("call", None)):
                    self.myLogWarning("%s - Erreur call"%(self.get_PDL_ID(), ))
                    # Erreur lors du call...
                    # Erreur lors du call...
                    self.updateTimeLastCall()
                    self.updateStatusLastCall( False )
                    self.updateErrorLastCall( "%s"%(self.getLastAnswer()))
                    self.myLogWarning( "%s - %s" %(self.get_PDL_ID(), self.getLastMethodCall()))
                else:
                    self.myLogWarning("Erreur inconnue call ERROR %s" %(inst))
                    self.myLogWarning("Erreur last answer %s" %(inst))
                    self.updateStatusLastCall( False )
                    self.updateTimeLastCall()
                    self.updateErrorLastCall("%s" %(inst))
                    self.myLogWarning(self.getLastMethodCall())

        else:
            self.setUpdateRealise( False )
            self.myLogWarning("%s pas d'update trop tot !!!" %(self.get_PDL_ID()))
        self.updateLastUpdate()
