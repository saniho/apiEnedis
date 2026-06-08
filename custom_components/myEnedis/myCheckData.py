from . import apiconst as API
from .exceptions import EnedisApiError, EnedisAuthError, EnedisDataError


_OK_ERRORS_CONTRACT = {"ADAM-DC-0008", "ADAM-ERR0069", "UNKERROR_002"}
_OK_ERRORS_DATA = {"ADAM-ERR0123", "ADAM-ERR0069", "no_data_found", "UNKERROR_002"}


class myCheckData:
    def _check_errors(self, dataAnswer, ok_errors=None):
        if ok_errors is None:
            ok_errors = set()
        if dataAnswer.get(API.ERROR_CODE, 200) == 500:
            return False
        if API.ERROR_CODE in dataAnswer:
            code = dataAnswer[API.ERROR_CODE]
            if code in ok_errors:
                return False
            if code == "ADAM-ERR0075":
                return False
            if code == "Internal Server error":
                raise EnedisApiError("UNKERROR_001")
            if code == "no_data_found":
                raise EnedisDataError(
                    "Collecte de données non activée sur le site enedis.fr"
                )
            raise EnedisApiError(code)
        if "_error" in dataAnswer and dataAnswer.get(API.USER_ALERT):
            raise EnedisAuthError(
                dataAnswer[API.ERROR], dataAnswer[API.DESCRIPTION]
            )
        return None

    def analyseValueAndAdd(self, data):
        if data is None:
            raise EnedisDataError("call", None)
        tot = 0
        if API.METER_READING in data:
            for x in data[API.METER_READING]["interval_reading"]:
                tot += int(x["value"])
        return tot

    def analyseValueAndMadeDico(self, data):
        if data is None:
            raise EnedisDataError("call", None)
        dicoLast7days = []
        if API.METER_READING in data:
            for x in reversed(data[API.METER_READING]["interval_reading"]):
                days = {"date": x["date"], "value": int(x["value"])}
                dicoLast7days.append(days)
        return dicoLast7days

    def analyseValue(self, data):
        if data is None:
            return None
        if API.METER_READING in data:
            return int(data[API.METER_READING]["interval_reading"][0]["value"])
        return None

    def analyseValueEcoWatt(self, data):
        if data is None:
            return None
        from datetime import datetime
        listeEcoWattDate = {}
        if "detail" in data:
            return listeEcoWattDate
        for date in data:
            for detailDate in data[date]["detail"]:
                detailDatekey = datetime.strptime(detailDate, "%Y-%m-%d %H:%M:%S")
                listeEcoWattDate[detailDatekey] = data[date]["detail"][detailDate]
        return listeEcoWattDate

    def analyseValueTempo(self, data):
        if data is None:
            return None
        from datetime import datetime
        listeTempoDate = {}
        for date in data:
            detailDatekey = datetime.strptime(date, "%Y-%m-%d")
            listeTempoDate[detailDatekey] = data[date]
        return listeTempoDate

    def checkData(self, dataAnswer):
        result = self._check_errors(dataAnswer, _OK_ERRORS_CONTRACT)
        if result is not None:
            return result
        return API.METER_READING in dataAnswer

    def checkDataPeriod(self, dataAnswer):
        result = self._check_errors(dataAnswer, _OK_ERRORS_DATA)
        if result is not None:
            return result
        return API.METER_READING in dataAnswer

    def checkDataEcoWatt(self, dataAnswer):
        result = self._check_errors(dataAnswer, _OK_ERRORS_DATA)
        if result is not None:
            return result
        return True

    def checkDataTempo(self, dataAnswer):
        result = self._check_errors(dataAnswer, _OK_ERRORS_DATA)
        if result is not None:
            return result
        return True
