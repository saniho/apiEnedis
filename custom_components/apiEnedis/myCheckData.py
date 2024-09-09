from . import apiconst as API


class myCheckData:
    def __init__(self):
        # pas d'init defini
        pass

    def analyseValueAndAdd(self, data):
        # print(data)
        if data is None:  # pas de valeur
            raise Exception("call", None)
        else:
            tot = 0
            if API.METER_READING in data.keys():  # meter reading present
                for x in data[API.METER_READING]["interval_reading"]:
                    tot += int(x["value"])
            return tot

    def analyseValueAndMadeDico(self, data):
        dicoLast7days = []
        if data is None:  # pas de valeur
            raise Exception("call", None)
        else:
            niemejour = 0
            if API.METER_READING in data.keys():  # meter reading present
                for x in reversed(data[API.METER_READING]["interval_reading"]):
                    niemejour += 1
                    days = {}
                    days["date"] = x["date"]
                    days["niemejour"] = niemejour
                    days["value"] = int(x["value"])
                    dicoLast7days.append(days)
        return dicoLast7days

    def analyseValue(self, data):
        if data is None:  # pas de valeur
            return None
        else:
            if API.METER_READING in data.keys():
                return int(data[API.METER_READING]["interval_reading"][0]["value"])
            else:
                return None

    def analyseValueEcoWatt(self, data):
        listeEcoWattDate = {}
        if data is None:  # pas de valeur
            return None
        else:
            from datetime import datetime
            for date in data.keys():
                # si pas de données
                if "detail" in data.keys():
                    return listeEcoWattDate
                for detailDate in data[date]["detail"]:
                    detailDatekey = datetime.strptime(detailDate, "%Y-%m-%d %H:%M:%S")
                    listeEcoWattDate[detailDatekey] = data[date]["detail"][detailDate]
            return listeEcoWattDate

    def analyseValueTempo(self, data):
        listeEcoWattDate = {}
        if data is None:  # pas de valeur
            return None
        else:
            from datetime import datetime
            for date in data.keys():
                detailDatekey = datetime.strptime(date, "%Y-%m-%d")
                listeEcoWattDate[detailDatekey] = data[date]
            return listeEcoWattDate

    def checkData(self, dataAnswer):
        # new version de la réponse
        # si erreur 500
        if dataAnswer.get(API.ERROR_CODE, 200) == 500:
            return False
        if API.ERROR_CODE in dataAnswer.keys():
            # point dans le mauvais sens de lecture
            if dataAnswer[API.ERROR_CODE] == "ADAM-ERR0069":
                return False
            # collecte horaire non activée
            if dataAnswer[API.ERROR_CODE] == "ADAM-ERR0075":
                return False
            # no_data_found
            if dataAnswer[API.ERROR_CODE] == "no_data_found":
                raise Exception(
                    "call",
                    "error",
                    "Collecte de données non activée sur le site enedis.fr",
                )
            # No consent can be found for this customer and this usage point
            if dataAnswer[API.ERROR_CODE] in [
                "ADAM-DC-0008",
                "ADAM-ERR0069",
                "UNKERROR_002",
            ]:
                return False
            if dataAnswer[API.ERROR_CODE] == "Internal Server error":
                # erreur interne enedis
                raise Exception("call", "error", "UNKERROR_001")
            else:
                raise Exception("call", "error", dataAnswer[API.ERROR_CODE])
        if "_error" in dataAnswer.keys():  # TODO a reactiver plus tard !!!
            # y a t il une erreur de consentement
            if dataAnswer[API.USER_ALERT]:
                raise Exception(
                    "call",
                    "error_user_alert",
                    dataAnswer[API.ERROR],
                    dataAnswer[API.DESCRIPTION],
                )
        if API.METER_READING not in dataAnswer.keys():
            return False
        return True

    def checkDataPeriod(self, dataAnswer):
        if dataAnswer.get(API.ERROR_CODE, 200) == 500:
            return False
        if API.ERROR_CODE in dataAnswer.keys():
            if (
                (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0123")
                or (dataAnswer[API.ERROR_CODE] == "no_data_found")
                or (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0069")
                or (dataAnswer[API.ERROR_CODE] == "UNKERROR_002")
            ):
                return False
            # collecte horaire non activée
            if dataAnswer[API.ERROR_CODE] == "ADAM-ERR0075":
                return False
            if dataAnswer[API.ERROR_CODE] == "Internal Server error":
                # erreur interne enedis
                raise Exception("call", "error", "UNKERROR_001")
            else:
                raise Exception("call", "error", dataAnswer[API.ERROR_CODE])
        if API.METER_READING not in dataAnswer.keys():
            return False
        return True

    def checkDataEcoWatt(self, dataAnswer):
        if dataAnswer.get(API.ERROR_CODE, 200) == 500:
            return False
        if API.ERROR_CODE in dataAnswer.keys():
            if (
                (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0123")
                or (dataAnswer[API.ERROR_CODE] == "no_data_found")
                or (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0069")
                or (dataAnswer[API.ERROR_CODE] == "UNKERROR_002")
            ):
                return False
            # collecte horaire non activée
            if dataAnswer[API.ERROR_CODE] == "ADAM-ERR0075":
                return False
            if dataAnswer[API.ERROR_CODE] == "Internal Server error":
                # erreur interne enedis
                raise Exception("call", "error", "UNKERROR_001")
            else:
                raise Exception("call", "error", dataAnswer[API.ERROR_CODE])
        return True

    def checkDataTempo(self, dataAnswer):
        if dataAnswer.get(API.ERROR_CODE, 200) == 500:
            return False
        if API.ERROR_CODE in dataAnswer.keys():
            if (
                (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0123")
                or (dataAnswer[API.ERROR_CODE] == "no_data_found")
                or (dataAnswer[API.ERROR_CODE] == "ADAM-ERR0069")
                or (dataAnswer[API.ERROR_CODE] == "UNKERROR_002")
            ):
                return False
            # collecte horaire non activée
            if dataAnswer[API.ERROR_CODE] == "ADAM-ERR0075":
                return False
            if dataAnswer[API.ERROR_CODE] == "Internal Server error":
                # erreur interne enedis
                raise Exception("call", "error", "UNKERROR_001")
            else:
                raise Exception("call", "error", dataAnswer[API.ERROR_CODE])
        return True
