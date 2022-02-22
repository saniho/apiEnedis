import datetime
import json

from custom_components.apiEnedis.myClientEnedis import myClientEnedis
from custom_components.apiEnedis.sensorEnedis import manageSensorState

contractJsonFile = "tests/Json/Contract/contract1.json"


def loadJsonFile(filename):
    with open(filename) as json_file:
        dataJson = json.load(json_file)
    return dataJson


def test_no_contract():
    myE = myClientEnedis("myToken", "myPDL")
    contract = myE.getContract()
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
    assert isinstance(contract.getValue(), dict), "bad initial value"
    assert contract._getHCHPfromHour(4) is True, "bad value"
    dateStr = "2022-01-01"
    assert contract.minCompareDateContract(dateStr) == "2022-01-01"
    assert contract.maxCompareDateContract(dateStr) is None

    contract.updateHCHP()  # Update HC from None to []
    assert contract.getHeuresCreuses() == []

    # Not tested:
    # contract.updateContract(self, None)


def test_update_contract():
    myE = myClientEnedis("myToken", "myPDL")
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    assert myE.getContract().getsubscribed_power() == "9 kVA", "bad subscribed"
    assert myE.getContract().getoffpeak_hours() == "HC (23H30-7H30)", "bad hour"
    assert (
        myE.getContract().getLastActivationDate() == "2007-07-06"
    ), "bad date activation"
    dataCompare = [["23:30", "23:59"], ["00:00", "07:30"]]
    assert (
        myE.getContract().getcleanoffpeak_hours() == dataCompare
    ), "erreur format HC/HP"


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
    myE.getContract().updateHCHP()
    dataCompare = [["00:00", "05:00"], ["22:00", "24:00"]]
    assert myE.getContract().getHeuresCreuses() == dataCompare, "erreur format HC/HP 1"
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
    myE.getContract().updateHCHP()
    dataCompare = []
    assert myE.getContract().getHeuresCreuses() == dataCompare, "erreur format HC/HP 2"


def test_update_last7days():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("tests/Json/Week/week1.json")
    myE.updateLast7Days(dataJson)
    dataCompare = [
        {"date": "2020-12-09", "niemejour": 1, "value": 42951},
        {"date": "2020-12-08", "niemejour": 2, "value": 35992},
        {"date": "2020-12-07", "niemejour": 3, "value": 46092},
        {"date": "2020-12-06", "niemejour": 4, "value": 37753},
        {"date": "2020-12-05", "niemejour": 5, "value": 38623},
        {"date": "2020-12-04", "niemejour": 6, "value": 38633},
        {"date": "2020-12-03", "niemejour": 7, "value": 33665},
    ]
    # assert myE.getLast7Days().getValue() == dataCompare, "Error last7Days"


def test_update_last_month():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("tests/Json/Month/month1.json")
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
    myE = call_update_current_month("tests/Json/Month/currentMonth1.json")
    assert myE.getCurrentMonth().getValue() == 242475, "Erreur currentMonth"
    # try:
    #    myE = call_update_current_month("tests/Json/Month/currentMonthError1.json")
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
    myE = call_update_yesterday("tests/Json/Yesterday/yesterday1.json")
    assert myE.getYesterday().getValue() == 42951, "Erreur yesterday"


def test_update_yesterdayHCHP():
    myE = call_update_yesterdayHCHP("tests/Json/Yesterday/yesterdayDetail1.json")
    mSS = manageSensorState()
    mSS.init(myE)
    laDate = datetime.date.today() - datetime.timedelta(60)
    mSS.getStatusHistory(laDate)


def test_update_yesterday_error():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("tests/Json/Error/error1.json")
    try:
        myE.updateYesterday(dataJson, withControl=False)
    except Exception as e:
        assert e.args[2] == "UNKERROR_001", "Erreur UNKERROR_001"


# def test_updateProductionYesterday():
#    myE = myClientEnedis("myToken", "myPDL")
#    dataJson = loadJsonFile("tests/Json/Production/error1.json")
#    myE.updateProductionYesterday( dataJson )
#    assert myE.getProductionYesterday() == 0, "Erreur production Value"


def test_updateProductionYesterday2():
    myE = myClientEnedis("myToken", "myPDL")
    dataJsonContrat = loadJsonFile("tests/Json/Contract/contract1.json")
    myE.updateContract(dataJsonContrat)
    dataJson = loadJsonFile("tests/Json/Production/error2.json")
    myE.updateYesterdayProduction(dataJson, withControl=False)
    assert myE.getProductionYesterday().getValue() == 0, "Erreur production Value"


def test_horaire_surcharge():
    hc = [["23:30", "23:59"], ["00:00", "07:35"]]
    myE = myClientEnedis("myToken", "myPDL", heuresCreuses=hc)
    dataJson = loadJsonFile(contractJsonFile)
    myE.updateContract(dataJson)
    myE.getContract().updateHCHP()
    dataCompare = hc
    assert myE.getContract().getHeuresCreuses() == dataCompare, "erreur format HC/HP"


def test_get_message():
    pass
    # assert False is False, "message errone"


def test_get_init():
    from custom_components.apiEnedis import sensorEnedis

    se = sensorEnedis.manageSensorState()
    assert se.getInit() is False, "not False !! "


def test_error_contract():
    myE = myClientEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Error/error.json")
    try:
        myE.updateContract(dataJson)
    except:
        print(myE.getErrorLastCall())
