from __future__ import annotations

import datetime
import json
import logging
import os

import pytest
import requests_mock

from custom_components.apiEnedis.myClientEnedis import myClientEnedis
from custom_components.apiEnedis.sensorEnedis import manageSensorState

JSON_DIR = os.path.dirname(__file__) + "/Json/"

contractJsonFile = "Contract/contract1.json"

LOGGER = logging.getLogger(__name__)


def loadJsonFile(filename):
    with open(JSON_DIR + filename) as json_file:
        dataJson = json.load(json_file)
    return dataJson


def loadFile(filename):
    with open(JSON_DIR + filename) as file:
        data = file.read()
    return data


def test_version():
    from custom_components.apiEnedis.const import __VERSION__

    manifest = loadJsonFile("../../custom_components/apiEnedis/manifest.json")
    assert __VERSION__ == manifest["version"]

    import packaging.version

    # Ensure 'v' in version does not interfere
    assert packaging.version.parse("v1.5.0.3") == packaging.version.parse("1.5.0.3")
    assert packaging.version.parse("v1.5.0.2") > packaging.version.parse("1.5.0.1")
    v1 = packaging.version.parse("v1.5.0.2")
    v2 = packaging.version.parse("v1.5.0.3")
    v3 = packaging.version.parse("v1.5.1")
    assert v2 > v1  # 2nd long version is newer
    assert v3 > v2  # 3rd short version is newer

    myE = call_update_yesterdayHCHP("Yesterday/yesterdayDetail1.json")
    mSS = manageSensorState()
    mSS.init(myE, version="v1.4.0.3")

    gitVersion = myE.getGitVersion()
    assert gitVersion is not None

    status, _ = mSS.getStatus()
    assert "v1.4.0.3" == status["version"]
    assert gitVersion == status["versionGit"]
    # v1.4.0.3 is old version, so update is available
    assert status["versionUpdateAvailable"] is True

    mSS.init(myE, version="v99.9.9")
    status, _ = mSS.getStatus()

    # 99.9.9 is futurist current version, so no update is available
    assert "v99.9.9" == status["version"]
    assert status["versionUpdateAvailable"] is False


def test_no_contract():
    myE = myClientEnedis("myToken", "myPDL")
    contract = myE.contract
    assert contract.getsubscribed_power() == "???", "bad subscribed initialisation"
    assert contract.getoffpeak_hours() == ()
    assert contract.getHeuresCreuses() is None
    assert contract.getcleanoffpeak_hours() == []
    assert contract.getLastActivationDate() is None, "bad date initialisation"
    assert contract.get_PDL_ID() == "myPDL", "bad PDL ID initialisation"
    assert contract.get_token() == "myToken", "bad token initialisation"
    assert contract.get_version() == "0.0.0", "bad version initialisation"
    assert contract.getUsagePointStatus() is None, "bad usage point initialisation"
    assert contract.getTypePDL() is None, "bad usage PDL type initialisation"
    assert contract.isLoaded is False, "bad initial value"
    assert contract._getHCHPfromHour(4) is True, "bad value"
    dateStr = "2022-01-01"
    assert contract.minCompareDateContract(dateStr) == "2022-01-01"
    assert contract.maxCompareDateContract(dateStr) is None

    contract.updateHCHP()  # Update HC from None to []
    assert contract.getHeuresCreuses() == []

    # Not tested:
    # contract.updateContract(self, None)


@pytest.fixture(params=[datetime.datetime(2020, 12, 25, 17, 5, 55)])
def patch_datetime_now(request, monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return request.param

    class mydate(datetime.date):
        @classmethod
        def today(cls):
            return request.param.date()

    monkeypatch.setattr(datetime, "datetime", mydatetime)
    monkeypatch.setattr(datetime, "date", mydate)


def test_init_contract(patch_datetime_now):
    dataFile = loadFile(contractJsonFile)

    with requests_mock.Mocker() as m:
        m.post("https://enedisgateway.tech/api", text=dataFile)
        myE = myClientEnedis("myToken", "myPDL")
        myE.getData()
        assert myE.contract.getsubscribed_power() == "9 kVA", "bad subscribed"
        assert myE.contract.getoffpeak_hours() == "HC (23H30-7H30)", "bad hour"
        assert (
            myE.contract.getLastActivationDate() == "2007-07-06"
        ), "bad date activation"
        dataCompare = [["23:30", "23:59"], ["00:00", "07:30"]]
        assert (
            myE.contract.getcleanoffpeak_hours() == dataCompare
        ), "erreur format HC/HP"


def test_update_contract():
    myE = myClientEnedis("myToken", "myPDL")
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    assert myE.contract.getsubscribed_power() == "9 kVA", "bad subscribed"
    assert myE.contract.getoffpeak_hours() == "HC (23H30-7H30)", "bad hour"
    assert myE.contract.getLastActivationDate() == "2007-07-06", "bad date activation"
    dataCompare = [["23:30", "23:59"], ["00:00", "07:30"]]
    assert myE.contract.getcleanoffpeak_hours() == dataCompare, "erreur format HC/HP"


def test_heures_creuses():
    myE = myClientEnedis("myToken", "myPDL")
    heureCreusesCh = eval("[['00:00','05:00'], ['22:00', '24:00']]")
    heuresCreusesON = True
    myE = myClientEnedis(
        "myToken",
        "myPDL",
        heuresCreuses=heureCreusesCh,
        heuresCreusesON=heuresCreusesON,
    )
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    myE.contract.updateHCHP()
    dataCompare = [["00:00", "05:00"], ["22:00", "24:00"]]
    assert myE.contract.getHeuresCreuses() == dataCompare, "erreur format HC/HP 1"
    # ***********
    heureCreusesCh = None
    heuresCreusesON = False
    myE = myClientEnedis(
        "myToken",
        "myPDL",
        heuresCreuses=heureCreusesCh,
        heuresCreusesON=heuresCreusesON,
    )
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    myE.contract.updateHCHP()
    dataCompare = []
    assert myE.contract.getHeuresCreuses() == dataCompare, "erreur format HC/HP 2"


@pytest.mark.usefixtures("patch_datetime_now")
@pytest.mark.parametrize(
    "patch_datetime_now", [(datetime.datetime(2020, 12, 9, 11, 22, 00))], indirect=True
)
def test_update_last7days(caplog):
    caplog.set_level(logging.DEBUG)  # Aide au debogue
    myE = myClientEnedis(
        "myToken",
        "myPDL",
        heuresCreuses=eval("[['00:00','05:00'], ['22:00', '24:00']]"),
        heuresCreusesON=True,
    )

    dataJsonContrat = loadJsonFile(contractJsonFile)
    LOGGER.debug("Chargement CONTRAT")
    myE.updateContract(dataJsonContrat)

    with requests_mock.Mocker() as m:
        dataJson = loadJsonFile("Week/week2.json")
        LOGGER.debug("Chargement WEEK1")

        dataFile = loadFile("Week/week1.json")
        m.post("https://enedisgateway.tech/api", text=dataFile)

        # La igne suitante déclenche un appel HTTP, d'ou le mock
        myE.updateLast7DaysDetails(data=dataJson, withControl=False)
    data = (
        myE.getLast7DaysDetails().getDaysHP(),
        myE.getLast7DaysDetails().getDaysHC(),
    )
    dataExpected = (
        {
            "2022-03-01": 13199.0,
            "2022-03-02": 14112.0,
            "2022-03-05": 21588.0,
            "2022-03-06": 23683.0,
            "2022-03-07": 34041.0,
        },
        {
            "2022-03-01": 14793.0,
            "2022-03-02": 8245.0,
            "2022-03-05": 10011.0,
            "2022-03-06": 8533.0,
            "2022-03-07": 8852.0,
        },
    )
    LOGGER.debug("Last7Days Data = %s", data)
    assert dataExpected == data, "Error last7Days"


def test_update_last_month():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("Month/month1.json")
    myE.updateLastMonth(dataJson, withControl=False)
    assert myE.getLastMonth().getValue() == 876699, "Error LastMonthData"


def call_update_current_month(fileName):
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile(fileName)
    myE.updateCurrentMonth(dataJson, withControl=False)
    return myE


def test_update_current_month():
    myE = call_update_current_month("Month/currentMonth1.json")
    assert myE.getCurrentMonth().getValue() == 242475, "Erreur currentMonth"
    # try:
    #    myE = call_update_current_month("Month/currentMonthError1.json")
    # except Exception as e:
    #    assert e.args[2] == "UNKERROR_001", "Erreur UNKERROR_001"


def call_update_yesterday(filename):
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile(filename)
    myE.updateYesterday(dataJson, withControl=False)
    return myE


def call_update_yesterdayHCHP(filename):
    myE = myClientEnedis("myToken", "myPDL")
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    dataJson = loadJsonFile(filename)
    yesterdayDate = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
    myE.updateDataYesterdayHCHP(dataJson, yesterdayDate, withControl=False)
    return myE


def test_update_yesterday():
    myE = call_update_yesterday("Yesterday/yesterday1.json")
    assert myE.getYesterday().getValue() == 42951, "Erreur yesterday"


def test_update_yesterdayHCHP():
    myE = call_update_yesterdayHCHP("Yesterday/yesterdayDetail1.json")
    mSS = manageSensorState()
    mSS.init(myE)
    laDate = datetime.date.today() - datetime.timedelta(60)
    mSS.getStatusHistory(laDate)


def test_update_yesterday_error():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("Error/error1.json")
    try:
        myE.updateYesterday(dataJson, withControl=False)
    except Exception as e:
        assert e.args[2] == "UNKERROR_001", "Erreur UNKERROR_001"


# def test_updateProductionYesterday():
#    myE = myClientEnedis("myToken", "myPDL")
#    dataJson = loadJsonFile("Production/error1.json")
#    myE.updateProductionYesterday( dataJson )
#    assert myE.getProductionYesterday() == 0, "Erreur production Value"


def test_updateProductionYesterday2():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("Production/error2.json")
    myE.updateYesterdayProduction(dataJson, withControl=False)
    assert myE.getProductionYesterday().getValue() == 0, "Erreur production Value"


def test_horaire_surcharge():
    hc = [["23:30", "23:59"], ["00:00", "07:35"]]
    myE = myClientEnedis("myToken", "myPDL", heuresCreuses=hc)
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    myE.contract.updateHCHP()
    dataCompare = hc
    assert myE.contract.getHeuresCreuses() == dataCompare, "erreur format HC/HP"


def test_get_message():
    pass
    # assert False is False, "message errone"


def test_get_init():
    from custom_components.apiEnedis import sensorEnedis

    se = sensorEnedis.manageSensorState()
    assert se.getInit() is False, "not False !! "


def test_error_contract():
    myE = myClientEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("Error/error.json")
    try:
        myE.updateContract(dataJson)
    except:
        print(myE.getErrorLastCall())
