import requests
import datetime, time
import json


class apiEnedis:
    def __init__(self, token, PDL_ID, delai = 3600):
        self._token = token
        self._PDL_ID = PDL_ID
        self._lastMonth = None
        self._lastYear = None
        self._currentMonth = None
        self._currentYear = None
        self._yesterday = None
        self._lastUpdate = None
        self._timeLastUpdate = None
        self._statusLastCall = False
        self._delai = delai
        pass

    def post_and_get_json(self, url, params=None, data=None, headers=None):
        try:
            import logging
            import json

            response = requests.post(url, params=params, data=json.dumps(data), headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as error:
            print('%s: %s', error.response.status_code, error.response.text)
            return None

    def getDataPeriod(self, deb, fin ):
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
        #s = """{"error":"result_400","enedis_return":{"error":"ADAM-ERR0123","error_description":"The requested period cannot be anterior to the meter's last activation date","error_uri":"https://bluecoder.enedis.fr/api-doc/consulter-souscrire"}}"""
        #dataAnswer = json.loads(s)
        #print("dataAnswer", dataAnswer)
        #return dataAnswer

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

    def analyseValue(self, data):
        if ( data == None ): #pas de valeur
            return None
        else:
            return int(data["meter_reading"]["interval_reading"][0]["value"])

    def getYesterday(self):
        return self._yesterday

    def getCurrentWeek(self):
        data = self.CallgetCurrentWeek()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot

    def getLastWeek(self):
        data = self.CallgetLastWeek()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot



    def updateYesterday(self, data=None):
        if ( data == None ): data = self.CallgetYesterday()
        self._yesterday = self.analyseValue( data )

    def checkDataPeriod(self, dataAnswer ):
        if ("error" in dataAnswer.keys()):
            raise Exception( 'call' , "error", dataAnswer['enedis_return']["error"] )

    def getLastMonth(self):
        return self._lastMonth
    def updateLastMonth(self, data=None):
        if ( data == None ): data = self.CallgetLastMonth()
        self.checkDataPeriod(data)
        self._lastMonth = self.analyseValueAndAdd( data )

    def getCurrentMonth(self):
        return self._currentMonth
    def updateCurrentMonth(self, data=None):
        if ( data == None ): data = self.CallgetCurrentMonth()
        print("data", data)
        self.checkDataPeriod(data)
        self._currentMonth = self.analyseValueAndAdd( data )

    def getLastYear(self):
        return self._lastYear
    def updateLastYear(self, data=None):
        if ( data == None ): data = self.CallgetLastYear()
        self.checkDataPeriod(data)
        self._lastYear =  self.analyseValueAndAdd( data )

    def getCurrentYear(self):
        return self._currentYear
    def updateCurrentYear(self, data=None):
        if ( data == None ): data = self.CallgetCurrentYear()
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
                    self.updateCurrentMonth()
                    self.updateLastMonth()
                    self.updateCurrentYear()
                    self.updateLastYear()
                    self.updateTimeLastCall()
                    self.updateStatusLastCall( True )
                except Exception as inst:
                    print("ici", inst.args[:2])
                    if ( inst.args[:2] == ("call", "error")): # gestion que c'est pas une erreur de contrat trop recent ?
                        print("Erreur call ERROR ", inst)
                        # Erreur lors du call...
                        self.updateTimeLastCall()
                        self.updateStatusLastCall( True )
            except Exception as inst:
                if ( inst.args == ("call", None)):
                    print("Erreur call")
                    # Erreur lors du call...
                    self.updateStatusLastCall( False )

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



    print( myDataEnedis.getYesterday(),
           myDataEnedis.getCurrentMonth(),
           myDataEnedis.getLastMonth(),
           myDataEnedis.getCurrentYear(),
           myDataEnedis.getLastYear() )
    print( myDataEnedis.getTimeLastCall(), myDataEnedis.getLastUpdate(), myDataEnedis.getStatusLastCall())
#
if __name__ == '__main__':
    main()

""" get all update and charge l'instance et utilisation avec get after ....."""
