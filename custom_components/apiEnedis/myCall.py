
try:
    from .const import (
        __nameMyEnedis__,
    )

except ImportError:
    from const import (
        __nameMyEnedis__,
    )
import logging
log = logging.getLogger(__nameMyEnedis__)
waitCall = 1  # 1 secondes

class myCall:
    def __init__(self):
        self._lastAnswer = None
        self._contentType = "application/json"
        self._contentHeaderMyEnedis = 'home-assistant-myEnedis'
        self._serverName = "https://enedisgateway.tech/api"
        pass

    def setParam( self, PDL_ID, token, version):
        self._PDL_ID, self._token, self._version = PDL_ID, token, version

    def getDefaultHeader(self):
        return {
            'Authorization': self._token,
            'Content-Type': self._contentType,
            'call-service': self._contentHeaderMyEnedis,
            'ha_sensor_myenedis_version': self._version,
        }

    def setLastAnswer(self, lastanswer):
        self._lastAnswer = lastanswer

    def getLastAnswer(self):
        return self._lastAnswer

    def post_and_get_json(self, url, params=None, data=None, headers=None):
        try_again = True
        nbEssai = 0
        dataAnswer = None
        while( try_again ):
            nbEssai += 1
            try:
                import time
                time.sleep( waitCall )
                import json, requests
                session = requests.Session()
                session.verify = True
                #print("ici", params, headers, data)
                log.info("====== Appel http !!! =====")
                response = session.post(url, params=params, data=json.dumps(data), headers=headers, timeout=30)
                response.raise_for_status()
                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)
                log.info("====== Appel http !!! headers : %s =====" %(headers))
                log.info("====== Appel http !!! data : %s =====" %(data))
                log.info("====== Appel http !!! reponse : %s =====" %(dataAnswer))
                #raise(requests.exceptions.Timeout) # pour raiser un timeout de test ;)
                try_again = False
            except requests.exceptions.Timeout as error:
                # a ajouter raison de l'erreur !!!
                log.error("====== Appel http !!! requests.exceptions.Timeout" )
                dataAnswer = {"enedis_return": {"error": "UNKERROR_002","message": "Timeout"}}
                self.setLastAnswer(dataAnswer)
            except requests.exceptions.HTTPError as error:
                log.info("====== Appel http !!! requests.exceptions.HTTPError" )
                if ( "ADAM-ERR0069" not in response.text ) and \
                        ( "__token_refresh_401" not in response.text ):
                    log.error("*" * 60)
                    log.error("header : %s " % (headers))
                    log.error("params : %s " % (params))
                    log.error("data : %s " % (json.dumps(data)))
                    log.error("Error JSON : %s " % (response.text))
                    log.error("*" * 60)
                #with open('error.json', 'w') as outfile:
                #    json.dump(response.json(), outfile)
                dataAnswer = response.json()
                self.setLastAnswer(dataAnswer)
                try_again = False
                if ( "usage_point_id parameter must be 14 digits long." in response.text):
                    try_again = True # si le nombre de digit n'est pas de 14 ...lié à une erreur coté enedis
            if ( try_again ) and ( nbEssai > 2):
                import time
                time.sleep(30) # on attend quelques secondes
                try_again = False
        return dataAnswer

    def getDataPeriod(self, deb, fin ):
        if (fin is not None):
            log.info("--get dataPeriod : %s => %s --" % (deb, fin))
            payload = {
                'type': 'daily_consumption',
                'usage_point_id': self._PDL_ID,
                'start': '%s' % (deb),
                'end': '%s' % (fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        return dataAnswer, callDone

    def getDataPeriodConsumptionMaxPower(self, deb, fin):
        if (fin is not None):
            log.info("--get dataPeriod : %s => %s --" % (deb, fin))
            payload = {
                'type': 'daily_consumption_max_power',
                'usage_point_id': self._PDL_ID,
                'start': '%s' % (deb),
                'end': '%s' % (fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataProductionPeriod(self, deb, fin):
        if (fin is not None):
            payload = {
                'type': 'daily_production',
                'usage_point_id': self._PDL_ID,
                'start': '%s' % (deb),
                'end': '%s' % (fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataPeriodCLC(self, deb, fin ):
        if (fin is not None):
            payload = {
                'type': 'consumption_load_curve',
                'usage_point_id': self._PDL_ID,
                'start': '%s' % (deb),
                'end': '%s' % (fin),
            }
            headers = self.getDefaultHeader()
            dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
            callDone = True
        else:
            # pas de donnée
            callDone = False
            dataAnswer = ""
        self.setLastAnswer(dataAnswer)
        return dataAnswer, callDone

    def getDataContract(self):
        payload = {
            'type': 'contracts',
            'usage_point_id': self._PDL_ID,
        }
        headers = self.getDefaultHeader()
        dataAnswer = self.post_and_get_json(self._serverName, data=payload, headers=headers)
        return dataAnswer
