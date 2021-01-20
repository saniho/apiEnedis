import json
from custom_components.apiEnedis import myEnedis

def loadJsonFile( filename ):
    with open(filename) as json_file:
        dataJson = json.load(json_file)
    return dataJson

def test_update_contract():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Contract/contract1.json")
    myE.updateContract(dataJson)
    assert myE.getsubscribed_power() == "9 kVA", "bad subscribed"
    assert myE.getoffpeak_hours() == "HC (23H30-7H30)", "bad hour"
    assert myE.isProduction() == False, "bad type production"
    assert myE.isConsommation() == True, "bad type consommation"
    assert myE.getLastActivationDate() == "2007-07-06", "bad date activation"
    dataCompare = [['23:30', '23:59'], ['00:00', '07:30']]
    assert myE.getcleanoffpeak_hours() == dataCompare, "erreur format HC/HP"

def test_heures_creuses():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    heureCreusesCh = eval("[['00:00','05:00'], ['22:00', '24:00']]")
    heuresCreusesON = True
    myE = myEnedis.myEnedis("myToken", "myPDL", heuresCreuses=heureCreusesCh,
                                     heuresCreusesON=heuresCreusesON)
    dataJson = loadJsonFile("tests/Json/Contract/contract1.json")
    myE.updateContract(dataJson)
    myE.updateHCHP()
    dataCompare = [['00:00', '05:00'], ['22:00', '24:00']]
    assert myE.getHeuresCreuses() == dataCompare, "erreur format HC/HP 1"
    #***********
    heureCreusesCh = None
    heuresCreusesON = False
    myE = myEnedis.myEnedis("myToken", "myPDL", heuresCreuses=heureCreusesCh,
                                     heuresCreusesON=heuresCreusesON)
    dataJson = loadJsonFile("tests/Json/Contract/contract1.json")
    myE.updateContract(dataJson)
    myE.updateHCHP()
    dataCompare = []
    assert myE.getHeuresCreuses() == dataCompare, "erreur format HC/HP 2"


def test_update_last7days():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Week/week1.json")
    myE.updateLast7Days(dataJson)
    dataCompare = [{'date': '2020-12-09', 'niemejour': 1, 'value': 42951},
                   {'date': '2020-12-08', 'niemejour': 2, 'value': 35992},
                   {'date': '2020-12-07', 'niemejour': 3, 'value': 46092},
                   {'date': '2020-12-06', 'niemejour': 4, 'value': 37753},
                   {'date': '2020-12-05', 'niemejour': 5, 'value': 38623},
                   {'date': '2020-12-04', 'niemejour': 6, 'value': 38633},
                   {'date': '2020-12-03', 'niemejour': 7, 'value': 33665}]
    assert myE.getLast7Days() == dataCompare, "Error last7Days"

def test_update_last_month():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Month/month1.json")
    myE.updateLastMonth(dataJson)
    assert myE.getLastMonth() == 876699, "Error LastMonthData"


def call_update_current_month( fileName ):
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile( fileName )
    myE.updateCurrentMonth(dataJson)
    return myE

def test_update_current_month():
    myE = call_update_current_month("tests/Json/Month/currentMonth1.json")
    assert myE.getCurrentMonth() == 242475, "Erreur currentMonth"
    try:
        myE = call_update_current_month("tests/Json/Month/currentMonthError1.json")
    except Exception as e:
        assert e.args[2] == "UNKERROR_001", "Erreur UNKERROR_001"

def call_update_yesterday( filename ):
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile( filename )
    myE.updateYesterday(dataJson)
    return myE

def test_update_yesterday():
    myE = call_update_yesterday( "tests/Json/Yesterday/yesterday1.json" )
    assert myE.getYesterday() == 42951, "Erreur yesterday"

def test_update_yesterday_error():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Error/error1.json")
    try:
        myE.updateYesterday(dataJson)
    except Exception as e:
        assert e.args[2] == "UNKERROR_001", "Erreur UNKERROR_001"

def test_updateProductionYesterday():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    dataJson = loadJsonFile("tests/Json/Production/error1.json")
    myE.updateProductionYesterday( dataJson )
    assert myE.getProductionYesterday() == 0, "Erreur production Value"

def test_horaire_surcharge():
    hc = [['23:30', '23:59'], ['00:00', '07:35']]
    myE = myEnedis.myEnedis("myToken", "myPDL", heuresCreuses = hc)
    dataJson = loadJsonFile("tests/Json/Contract/contract1.json")
    myE.updateContract(dataJson)
    myE.updateHCHP()
    dataCompare = hc
    assert myE._heuresCreuses == dataCompare, "erreur format HC/HP"

