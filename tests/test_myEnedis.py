from __future__ import annotations

import ast
import datetime
import json
import logging
import os

import pytest
import requests
import requests_mock

from custom_components.apiEnedis.myClientEnedis import myClientEnedis
from custom_components.apiEnedis.sensorEnedis import manageSensorState

JSON_DIR = os.path.dirname(__file__) + "/Json/"

contractJsonFile = "Contract/contract1.json"

ecoWattJsonFile = "EcoWatt/updateEcoWatt.json"

LOGGER = logging.getLogger(__name__)


def loadJsonFile(filename):
    with open(JSON_DIR + filename) as json_file:
        dataJson = json.load(json_file)
    return dataJson


def loadFile(filename):
    with open(JSON_DIR + filename) as file:
        data = file.read()
    return data


# def test_version():
#     from custom_components.apiEnedis.const import __VERSION__
#
#     manifest = loadJsonFile("../../custom_components/apiEnedis/manifest.json")
#     assert __VERSION__ == manifest["version"]
#
#     import packaging
#     import packaging.version
#
#     # Ensure 'v' in version does not interfere
#     assert packaging.version.parse("v1.5.0.3") == packaging.version.parse("1.5.0.3")
#     assert packaging.version.parse("v1.5.0.2") > packaging.version.parse("1.5.0.1")
#     v1 = packaging.version.parse("v1.5.0.2")
#     v2 = packaging.version.parse("v1.5.0.3")
#     v3 = packaging.version.parse("v1.5.1")
#     assert v2 > v1  # 2nd long version is newer
#     assert v3 > v2  # 3rd short version is newer
#
#     myE = call_update_yesterdayHCHP("Yesterday/yesterdayDetail1.json")
#     mSS = manageSensorState()
#     mSS.init(myE, version="v1.4.0.3")
#
#     # desactivé suite arret de l'usage de gitinformation
#     # gitVersion = myE.getGitVersion()
#     # assert gitVersion is not None
#
#     status, _ = mSS.getStatus()
#     assert "v1.4.0.3" == status["version"]
#     #assert gitVersion == status["versionGit"]
#     # v1.4.0.3 is old version, so update is available
#     assert status["versionUpdateAvailable"] is True
#
#     mSS.init(myE, version="v99.9.9")
#     status, _ = mSS.getStatus()
#
#     # 99.9.9 is futurist current version, so no update is available
#     assert "v99.9.9" == status["version"]
#     assert status["versionUpdateAvailable"] is False


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
    def _delta(timedelta=None, **kwargs):
        """Moves time fwd/bwd by the delta"""
        from datetime import timedelta as td

        if not timedelta:
            timedelta = td(**kwargs)
        request.param += timedelta

    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return request.param

        @classmethod
        def today(cls):
            # Recommend using now or date.today to use a single method
            raise Exception("Use now() or date.today()")
            return cls.now()

        @classmethod
        def utcnow(cls):
            # Recommend using now or date.today to use a single method
            raise Exception("Use now()")
            return cls.now()

        @classmethod
        def delta(cls, *args, **kwargs):
            _delta(*args, **kwargs)

    class mydate(datetime.date):
        @classmethod
        def today(cls):
            return request.param.date()

        @classmethod
        def delta(cls, *args, **kwargs):
            _delta(*args, **kwargs)

    monkeypatch.setattr(datetime, "datetime", mydatetime)
    monkeypatch.setattr(datetime, "date", mydate)


def test_init_contract(patch_datetime_now, caplog):
    caplog.set_level(logging.DEBUG)  # Aide au debogue
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


@pytest.mark.usefixtures("patch_datetime_now")
@pytest.mark.parametrize(
    "patch_datetime_now", [(datetime.datetime(2022, 3, 24, 21, 30, 00))], indirect=True
)
def test_update_data(caplog, tmpdir):
    caplog.set_level(logging.DEBUG)  # Aide au debogue
    myE = myClientEnedis(
        "myToken",
        "20000000000000",
        heuresCreuses=ast.literal_eval("[['00:00','05:00'], ['22:00', '24:00']]"),
        heuresCreusesON=True,
    )
    myE.setPathArchive(tmpdir)

    with requests_mock.Mocker() as m:
        URL = "https://enedisgateway.tech/api"

        # Two timeouts, requests will be aborted
        SEQUENCE_1 = [
            {"exc": requests.exceptions.ConnectTimeout},
            # {"text": loadFile("Sequence1/data_1.txt")},
            {"exc": requests.exceptions.ConnectTimeout},
        ]

        SEQUENCE_2 = [
            # Insertion d'une erreur de token qui arrive
            # en début d'une séquence - elle ne devrait pas faire
            # planter la séquence (si cela n'arrive qu'une fois)
            # - il faudrait que cela se produit au moins 2 fois.
            # Commenté car cela fait planter le test.
            # {"text": loadFile("Sequence1/data_token_error.txt")},
            # {"text": loadFile("Sequence1/data_1.txt")},
            {"text": loadFile("Sequence1/data_2.txt")},
            {"text": loadFile("Sequence1/data_3.txt")},
            {"text": loadFile("Sequence1/data_4.txt")},
            {"text": loadFile("Sequence1/data_5.txt")},
            {"text": loadFile("Sequence1/data_6.txt")},
            {"text": loadFile("Sequence1/data_7.txt")},
            {"text": loadFile("Sequence1/data_8.txt")},
            {"text": loadFile("Sequence1/data_9.txt")},
            {"text": loadFile("Sequence1/data_10.txt")},
            {"text": loadFile("Sequence1/data_11.txt")},
            {"text": loadFile("Sequence1/data_12.txt")},
            {"text": loadFile("Sequence1/data_13.txt")},
            {"text": loadFile("Sequence1/data_14.txt")},
            {"text": loadFile("Sequence1/data_15.txt")},
            {"text": loadFile("Sequence1/data_16.txt")},
            {"text": loadFile("Sequence1/data_17.txt")},
            {"text": loadFile("Sequence1/data_18.txt")},
        ]

        # Failing getData because of timeouts
        m.register_uri("POST", URL, SEQUENCE_1)
        success = myE.getData()

        # Failing getData because of previous timeouts, less than hour later
        LOGGER.debug("Test that fetches fail because of previous timeout")
        datetime.datetime.delta(minutes=30)  # type: ignore[attr-defined]
        m.register_uri("POST", URL, SEQUENCE_2)
        success = myE.getData()

        # Failing getData because of previous timeouts, more than hour later
        LOGGER.debug("Test that fetches succeed because previous timeout is old")
        datetime.datetime.delta(minutes=30, seconds=10)  # type: ignore[attr-defined]
        m.register_uri("POST", URL, SEQUENCE_2)
        success = myE.getData()

    assert success is True

    data = {
        "DaysHP": myE.getLast7DaysDetails().getDaysHP(),
        "DaysHC": myE.getLast7DaysDetails().getDaysHC(),
    }

    # dataExpected = {
    #     "DaysHP": {
    #         "2022-03-17": 5010.0,
    #         "2022-03-18": 4382.0,
    #         "2022-03-19": 8348.0,
    #         "2022-03-20": 7051.0,
    #         "2022-03-21": 4956.0,
    #         "2022-03-22": 5728.0,
    #         "2022-03-23": 5301.0,
    #     },
    #     "DaysHC": {
    #         "2022-03-17": 2059.0,
    #         "2022-03-18": 1777.0,
    #         "2022-03-19": 2330.0,
    #         "2022-03-20": 2691.0,
    #         "2022-03-21": 3140.0,
    #         "2022-03-22": 2363.0,
    #         "2022-03-23": 2190.0,
    #     },
    # }
    dataExpected = {
        'DaysHC': {'2022-03-17': 1906.0,
                    '2022-03-18': 1694.0,
                    '2022-03-19': 2178.0,
                    '2022-03-20': 2498.0,
                    '2022-03-21': 2573.0,
                    '2022-03-22': 2210.0,
                    '2022-03-23': 2004.0},
         'DaysHP': {'2022-03-17': 5163.0,
                    '2022-03-18': 4465.0,
                    '2022-03-19': 8500.0,
                    '2022-03-20': 7244.0,
                    '2022-03-21': 5523.0,
                    '2022-03-22': 5881.0,
                    '2022-03-23': 5487.0,
        },
    }

    LOGGER.debug("Data = %s", data)
    # desactivé pour le moment
    assert dataExpected == data, "Error data_update"

    stateExpected = {}
    gitVersion = myE.getGitVersion()
    # stateExpected = {
    #     "version": "v1.4.0.3",
    #     "versionGit": gitVersion,
    #     "versionUpdateAvailable": False,
    #     "nbCall": 16,
    #     "typeCompteur": "consommation",
    #     "numPDL": "20000000000000",
    #     "horaireMinCall": 1106,
    #     "activationDate": "2000-02-17",
    #     "lastUpdate": datetime.datetime(2022, 3, 24, 22, 30, 10),
    #     "timeLastCall": datetime.datetime(2022, 3, 24, 22, 30, 10),
    #     "yesterday": 7491,
    #     "last_week": 58459,
    #     "yesterdayDate": "2022-03-23",
    #     "yesterdayLastYear": 9378,
    #     "yesterdayLastYearDate": "2022-03-23",
    #     "yesterdayConsumptionMaxPower": 1798,
    #     "day_1_HP": 5301.0,
    #     "day_2_HP": 5728.0,
    #     "day_3_HP": 4956.0,
    #     "day_4_HP": 7051.0,
    #     "day_5_HP": 8348.0,
    #     "day_6_HP": 4382.0,
    #     "day_7_HP": 5010.0,
    #     "day_1_HC": 2190.0,
    #     "day_2_HC": 2363.0,
    #     "day_3_HC": 3140.0,
    #     "day_4_HC": 2691.0,
    #     "day_5_HC": 2330.0,
    #     "day_6_HC": 1777.0,
    #     "day_7_HC": 2059.0,
    #     "dailyweek_cost": ["0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"],
    #     "dailyweek_costHC": ["0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"],
    #     "dailyweek_HC": ["2.190", "2.363", "3.140", "2.691", "2.330", "1.777", "2.059"],
    #     "dailyweek": [
    #         "2022-03-23",
    #         "2022-03-22",
    #         "2022-03-21",
    #         "2022-03-20",
    #         "2022-03-19",
    #         "2022-03-18",
    #         "2022-03-17",
    #     ],
    #     "dailyweek_costHP": ["0.00", "0.00", "0.00", "0.00", "0.00", "0.00", "0.00"],
    #     "dailyweek_HP": ["5.301", "5.728", "4.956", "7.051", "8.348", "4.382", "5.010"],
    #     "day_1": "7.49",
    #     "day_2": "8.09",
    #     "day_3": "8.10",
    #     "day_4": "9.74",
    #     "day_5": "10.68",
    #     "day_6": "6.16",
    #     "day_7": "7.07",
    #     "daily": ["7.49", "8.09", "8.10", "9.74", "10.68", "6.16", "7.07"],
    #     "halfhourly": [],
    #     "offpeak_hours": [["00:00", "05:00"], ["22:00", "24:00"]],
    #     "peak_hours": "5.301",
    #     "peak_offpeak_percent": "70.76",
    #     "yesterday_HC_cost": "0.000",
    #     "yesterday_HP_cost": "0.000",
    #     "daily_cost": "0.00",
    #     "yesterday_HC": "2.190",
    #     "yesterday_HP": "5.301",
    #     "yesterday_HCHP": "7.491",
    #     "current_week": "23.678",
    #     "current_week_number": 12,
    #     "current_week_last_year": "26.878",
    #     "last_month": "256.446",
    #     "last_month_last_year": "267.103",
    #     "current_month": "193.788",
    #     "current_month_last_year": "208.641",
    #     "last_year": "3373.658",
    #     "current_year": "741.429",
    #     "errorLastCall": "",
    #     "errorLastCallInterne": "",
    #     "monthly_evolution": "-3.990",
    #     "year_evolution": "-78.023",
    #     "current_week_evolution": "-11.906",
    #     "current_month_evolution": "-7.119",
    #     "yesterday_evolution": "-20.122",
    #     "subscribed_power": "6 kVA",
    #     "offpeak_hours_enedis": "HC (0H54-6H54;11H54-13H54)",
    #     "yesterday_production": 0,
    #     "serviceEnedis": "enedisGateway",
    # }

    stateExpected = {
        'activationDate': '2000-02-17',
        'current_month': '193.788',
        'current_month_evolution': '-7.119',
        'current_month_last_year': '208.641',
        'current_week': '23.678',
        'current_week_evolution': '-11.906',
        'current_week_last_year': '26.878',
        'current_week_number': 12,
        'current_year': '741.429',
        'daily': ['7.49', '8.09', '8.10', '9.74', '10.68', '6.16', '7.07'],
        'daily_cost': '0.00',
        'dailyweek': ['2022-03-23',
                   '2022-03-22',
                   '2022-03-21',
                   '2022-03-20',
                   '2022-03-19',
                   '2022-03-18',
                   '2022-03-17'],
        'dailyweek_HC': ['2.004',
                      '2.210',
                      '2.573',
                      '2.498',
                      '2.178',
                      '1.694',
                      '1.906'],
        'dailyweek_HP': ['5.487',
                      '5.881',
                      '5.523',
                      '7.244',
                      '8.500',
                      '4.465',
                      '5.163'],
        'dailyweek_cost': ['0.00',
                        '0.00',
                        '0.00',
                        '0.00',
                        '0.00',
                        '0.00',
                        '0.00'],
        'dailyweek_costHC': ['0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00'],
        'dailyweek_costHP': ['0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00',
                          '0.00'],
        'day_1': '7.49',
        'day_1_HC': 2004.0,
        'day_1_HP': 5487.0,
        'day_2': '8.09',
        'day_2_HC': 2210.0,
        'day_2_HP': 5881.0,
        'day_3': '8.10',
        'day_3_HC': 2573.0,
        'day_3_HP': 5523.0,
        'day_4': '9.74',
        'day_4_HC': 2498.0,
        'day_4_HP': 7244.0,
        'day_5': '10.68',
        'day_5_HC': 2178.0,
        'day_5_HP': 8500.0,
        'day_6': '6.16',
        'day_6_HC': 1694.0,
        'day_6_HP': 4465.0,
        'day_7': '7.07',
        'day_7_HC': 1906.0,
        'day_7_HP': 5163.0,
        'errorLastCall': '',
        'errorLastCallInterne': '',
        'halfhourly': [],
        'horaireMinCall': 950,
        'lastUpdate': datetime.datetime(2022, 3, 24, 22, 30, 10),
        'last_month': '256.446',
        'last_month_last_year': '267.103',
        'last_week': 58459,
        'last_year': '3373.658',
        'monthly_evolution': '-3.990',
        'nbCall': 16,
        'numPDL': '20000000000000',
        'offpeak_hours': [['00:00', '05:00'], ['22:00', '24:00']],
        'offpeak_hours_enedis': 'HC (0H54-6H54;11H54-13H54)',
        'peak_hours': '5.301',
        'peak_offpeak_percent': '70.76',
        'serviceEnedis': 'enedisGateway',
        'subscribed_power': '6 kVA',
        'timeLastCall': datetime.datetime(2022, 3, 24, 22, 30, 10),
        'typeCompteur': 'consommation',
        'version': 'v1.4.0.3',
        'versionGit': '',
        'versionUpdateAvailable': False,
        'year_evolution': '-78.023',
        'yesterday': 7491,
        'yesterdayConsumptionMaxPower': 1798,
        'yesterdayDate': '2022-03-23',
        'yesterdayLastYear': 9378,
        'yesterdayLastYearDate': '2022-03-23',
        'yesterday_HC': '2.190',
        'yesterday_HCHP': '7.491',
        'yesterday_HC_cost': '0.000',
        'yesterday_HP': '5.301',
        'yesterday_HP_cost': '0.000',
        'yesterday_evolution': '-20.122',
        'yesterday_production': 0
    }

    mSS = manageSensorState()
    mSS.init(myE, version="v1.4.0.3")
    state, other = mSS.getStatus()
    stateExpected["horaireMinCall"] = state["horaireMinCall"]
    assert stateExpected == state


@pytest.mark.usefixtures("patch_datetime_now")
@pytest.mark.parametrize(
    "patch_datetime_now",
    [(datetime.datetime(2022, 3, 27, 9, 52, 37, 939458))],
    indirect=True,
)
def test_delay_after_error(caplog):
    caplog.set_level(logging.DEBUG)  # Aide au debogue

    lastTime = datetime.datetime(2022, 3, 26, 23, 27, 29, 20309)
    myE = myClientEnedis("myToken", "myPDL")
    myE.updateTimeLastCall(t=lastTime)
    result = myE.getDelayIsGoodAfterError(datetime.datetime.now())
    assert result is True


def test_heures_creuses():
    myE = myClientEnedis("myToken", "myPDL")
    heureCreusesCh = ast.literal_eval("[['00:00','05:00'], ['22:00', '24:00']]")
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
        heuresCreuses=ast.literal_eval("[['00:00','05:00'], ['22:00', '24:00']]"),
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


def test_updateEcoWatt():
    dataExpected = {datetime.datetime(2022, 12, 27, 0, 0): 1,
                    datetime.datetime(2022, 12, 27, 1, 0): 1,
                    datetime.datetime(2022, 12, 27, 2, 0): 1,
                    datetime.datetime(2022, 12, 27, 3, 0): 1,
                    datetime.datetime(2022, 12, 27, 4, 0): 1,
                    datetime.datetime(2022, 12, 27, 5, 0): 1,
                    datetime.datetime(2022, 12, 27, 6, 0): 1,
                    datetime.datetime(2022, 12, 27, 7, 0): 1,
                    datetime.datetime(2022, 12, 27, 8, 0): 1,
                    datetime.datetime(2022, 12, 27, 9, 0): 1,
                    datetime.datetime(2022, 12, 27, 10, 0): 1,
                    datetime.datetime(2022, 12, 27, 11, 0): 1,
                    datetime.datetime(2022, 12, 27, 12, 0): 1,
                    datetime.datetime(2022, 12, 27, 13, 0): 1,
                    datetime.datetime(2022, 12, 27, 14, 0): 1,
                    datetime.datetime(2022, 12, 27, 15, 0): 1,
                    datetime.datetime(2022, 12, 27, 16, 0): 1,
                    datetime.datetime(2022, 12, 27, 17, 0): 1,
                    datetime.datetime(2022, 12, 27, 18, 0): 1,
                    datetime.datetime(2022, 12, 27, 19, 0): 1,
                    datetime.datetime(2022, 12, 27, 20, 0): 1,
                    datetime.datetime(2022, 12, 27, 21, 0): 1,
                    datetime.datetime(2022, 12, 27, 22, 0): 1,
                    datetime.datetime(2022, 12, 27, 23, 0): 1,
                    datetime.datetime(2022, 12, 28, 0, 0): 1,
                    datetime.datetime(2022, 12, 28, 1, 0): 1,
                    datetime.datetime(2022, 12, 28, 2, 0): 1,
                    datetime.datetime(2022, 12, 28, 3, 0): 1,
                    datetime.datetime(2022, 12, 28, 4, 0): 1,
                    datetime.datetime(2022, 12, 28, 5, 0): 1,
                    datetime.datetime(2022, 12, 28, 6, 0): 1,
                    datetime.datetime(2022, 12, 28, 7, 0): 1,
                    datetime.datetime(2022, 12, 28, 8, 0): 1,
                    datetime.datetime(2022, 12, 28, 9, 0): 1,
                    datetime.datetime(2022, 12, 28, 10, 0): 1,
                    datetime.datetime(2022, 12, 28, 11, 0): 1,
                    datetime.datetime(2022, 12, 28, 12, 0): 1,
                    datetime.datetime(2022, 12, 28, 13, 0): 1,
                    datetime.datetime(2022, 12, 28, 14, 0): 1,
                    datetime.datetime(2022, 12, 28, 15, 0): 1,
                    datetime.datetime(2022, 12, 28, 16, 0): 1,
                    datetime.datetime(2022, 12, 28, 17, 0): 1,
                    datetime.datetime(2022, 12, 28, 18, 0): 1,
                    datetime.datetime(2022, 12, 28, 19, 0): 1,
                    datetime.datetime(2022, 12, 28, 20, 0): 1,
                    datetime.datetime(2022, 12, 28, 21, 0): 1,
                    datetime.datetime(2022, 12, 28, 22, 0): 1,
                    datetime.datetime(2022, 12, 28, 23, 0): 1}
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonEcoWatt = loadJsonFile(ecoWattJsonFile)
    myE.updateEcoWatt(dataJsonEcoWatt, withControl=False)
    assert myE.getEcoWatt().getValue() == dataExpected, "Erreur EcoWatt Value"


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
