
class myCheckData:
    def __init__(self):
        # pas d'init defini
        pass

    def analyseValueAndAdd(self, data):
        #print(data)
        if (data == None):  # pas de valeur
            raise Exception('call', None)
        else:
            tot = 0
            if ( "meter_reading" in data.keys()): # meter reading present
                for x in data["meter_reading"]["interval_reading"]:
                    tot += int(x["value"])
            return tot

    def analyseValueAndMadeDico(self, data):
        dicoLast7days = []
        if (data == None):  # pas de valeur
            raise Exception('call', None)
        else:
            niemejour = 0
            if ( "meter_reading" in data.keys()): # meter reading present
                for x in reversed(data["meter_reading"]["interval_reading"]):
                    niemejour += 1
                    days = {}
                    days['date'] = x['date']
                    days['niemejour'] = niemejour
                    days['value'] = int(x['value'])
                    dicoLast7days.append(days)
        return dicoLast7days

    def analyseValue(self, data):
        if (data == None):  # pas de valeur
            return None
        else:
            if ( "meter_reading" in data.keys()):
                return int(data["meter_reading"]["interval_reading"][0]["value"])
            else:
                return None

    def checkData(self, dataAnswer):
        # new version de la réponse
        # si erreur 500
        if (dataAnswer.get("error_code", 200) == 500):
            return False
        if ("error_code" in dataAnswer.keys()):
            # point dans le mauvais sens de lecture
            if (dataAnswer["error_code"] == "ADAM-ERR0069"):
                return False
            # collecte horaire non activée
            if (dataAnswer["error_code"] == "ADAM-ERR0075"):
                return False
            # no_data_found
            if (dataAnswer["error_code"] == "no_data_found"):
                raise Exception('call', "error", "Collecte de données non activée sur le site enedis.fr")
            # No consent can be found for this customer and this usage point
            if dataAnswer["error_code"] in ["ADAM-DC-0008", "ADAM-ERR0069", "UNKERROR_002"]:
                return False
            if (dataAnswer["error_code"] == "Internal Server error"):
                # erreur interne enedis
                raise Exception('call', "error", "UNKERROR_001")
            else:
                raise Exception('call', "error", dataAnswer["error_code"])
        if ( "meter_reading" not in dataAnswer.keys() ):
            return False
        return True


    def checkDataPeriod(self, dataAnswer):
        if (dataAnswer.get("error_code", 200) == 500):
            return False
        if ("error_code" in dataAnswer.keys()):
            if (dataAnswer["error_code"] == "ADAM-ERR0123") or \
                    (dataAnswer["error_code"] == "no_data_found") or \
                    (dataAnswer["error_code"] == "ADAM-ERR0069") or \
                    (dataAnswer["error_code"] == "UNKERROR_002"):
                return False
            # collecte horaire non activée
            if (dataAnswer["error_code"] == "ADAM-ERR0075"):
                return False
            if (dataAnswer["error_code"] == "Internal Server error"):
                # erreur interne enedis
                raise Exception('call', "error", "UNKERROR_001")
            else:
                raise Exception('call', "error", dataAnswer["error_code"])
        return True
