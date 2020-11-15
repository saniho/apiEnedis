import requests
import datetime, time
import json
import logging

__nameMyEnedis__ = "apiEnedis"
class apiEnedis:
    def __init__(self, token, PDL_ID, delai = 3600, log = None):
        self._token = token
        self._PDL_ID = PDL_ID
        self._lastMonth = None
        self._lastYear = None
        self._currentMonth = None
        self._currentYear = None
        self._lastWeek = None
        self._last7Days = None
        self._currentWeek = None
        self._yesterday = None
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall = False
        self._errorLastCall = None
        self._lastAnswer = None
        self._delai = delai
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

    def getDataPeriod2(self, deb, fin ):
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

    def CallgetCurrentWeek(self):
        import datetime
        today = datetime.date.today()
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        firstdateofweek = (datetime.date.today()-datetime.timedelta(days=datetime.datetime.today().weekday() % 7)).strftime("%Y-%m-%d")
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
        return self.getDataPeriod( debCurrentMonth, cejour)

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
                days[ 'jourName'] = x[ 'date']
                days[ 'niemejour'] = niemejour
                days[ 'value'] = x[ 'value']
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
        self._yesterday = self.analyseValue( data )

    def checkDataPeriod(self, dataAnswer ):
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
        self.checkDataPeriod(data)
        self._currentWeek = self.analyseValueAndAdd( data )

    def getCurrentMonth(self):
        return self._currentMonth
    def updateCurrentMonth(self, data=None):
        self.myLog("--updateCurrentMonth --")
        if ( data == None ): data = self.CallgetCurrentMonth()
        self.myLog("updateCurrentMonth : data %s" %(data))
        self.checkDataPeriod(data)
        self._currentMonth = self.analyseValueAndAdd( data )

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
                    self.updateLastYear()
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
                    self.updateStatusLastCall( False )
                else:
                    print("Erreur inconnue call ERROR ", inst)
                    print("Erreur last answer", inst)

        else:
            print("pas d'update trop tot !!!")
        self.updateLastUpdate()

def main():
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/security.txt")
    token = mon_conteneur['ENEDIS']['TOKEN']
    PDL_ID = mon_conteneur['ENEDIS']['CODE']
    myDataEnedis = apiEnedis( token, PDL_ID, delai = 10 ) # on fait un update 10 secondes après le dernier ok
    myDataEnedis.update()

    #myDataEnedis.updateLast7Days()

    print( myDataEnedis.getYesterday(),
           myDataEnedis.getCurrentMonth(),
           myDataEnedis.getLastMonth(),
           myDataEnedis.getCurrentWeek(),
           myDataEnedis.getLastWeek(),
           myDataEnedis.getLast7Days(),
           myDataEnedis.getCurrentYear(),
           myDataEnedis.getLastYear() )
    print( myDataEnedis.getTimeLastCall(), myDataEnedis.getLastUpdate(), myDataEnedis.getStatusLastCall())
    print( myDataEnedis.getErrorLastCall())

    last7days = myDataEnedis.getLast7Days()
    for day in last7days:
        print('day_%s' % (day["niemejour"]), day["value"] )
#
if __name__ == '__main__':
    main()

""" get all update and charge l'instance et utilisation avec get after ....."""