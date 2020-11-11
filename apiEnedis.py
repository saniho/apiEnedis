import requests
import datetime


class apiEnedis:
    def __init__(self, token, PDL_ID):
        self._token = token
        self._PDL_ID = PDL_ID
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
        #print( deb, fin )
        return self.post_and_get_json("https://enedisgateway.tech/api", data=payload, headers=headers)

    def CallgetYesterday(self):
        hier = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y-%m-%d")
        cejour = (datetime.date.today()).strftime("%Y-%m-%d")
        return self.getDataPeriod( hier, cejour )

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

    def getYesterday(self):
        data = self.CallgetYesterday()
        return int(data["meter_reading"]["interval_reading"][0]["value"])

    def getLastMonth(self):
        data = self.CallgetLastMonth()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot

    def getCurrentMonth(self):
        data = self.CallgetCurrentMonth()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot

    def getLastYear(self):
        data = self.CallgetLastYear()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot

    def getCurrentYear(self):
        data = self.CallgetCurrentYear()
        tot = 0
        for x in data["meter_reading"]["interval_reading"]:
            tot += int(x["value"])
        return tot


def main():
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/security.txt")
    token = mon_conteneur['ENEDIS']['TOKEN']
    PDL_ID = mon_conteneur['ENEDIS']['CODE']
    myDataEnedis = apiEnedis( token, PDL_ID )
    #dataYesterday = myDataEnedis.getYesterday()
    #dataLastMonth = myDataEnedis.getLastMonth()
    #dataCurrentMonth = myDataEnedis.getCurrentMonth()
    #dataCurrentYear = myDataEnedis.getCurrentYear()
    dataLastYear = myDataEnedis.getLastYear()
    #print(dataYesterday)
    #print(dataLastMonth)
    #print(dataCurrentMonth)
    #print(dataCurrentYear)
    print(dataLastYear)
#
if __name__ == '__main__':
    main()
