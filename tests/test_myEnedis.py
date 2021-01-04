import json
from custom_components.apiEnedis import myEnedis


def test_update_contract():
    myE = myEnedis.myEnedis("myToken", "myPDL")

    with open("./Json/Contract/contract1.json") as json_file:
        dataJson = json.load(json_file)
    myE.updateContract(dataJson)
    assert myE.getsubscribed_power() == "9 kVA", "bad subscribed"
    assert myE.getoffpeak_hours() == "HC (23H30-7H30)", "bad hour"
    assert myE.isProduction() == False, "bad type production"
    assert myE.isConsommation() == True, "bad type consommation"
    dataCompare = [['23:30', '23:59'], ['00:00', '07:30']]
    assert myE.getcleanoffpeak_hours() == dataCompare, "erreur format HC/HP"
    # print( myContract)
    # assert False


def test_update_last7days():
    myE = myEnedis.myEnedis("myToken", "myPDL")
    with open("./Json/Week/week1.json") as json_file:
        dataJson = json.load(json_file)
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
    with open("./Json/Month/month1.json") as json_file:
        dataJson = json.load(json_file)
    myE.updateLastMonth(dataJson)
    myE.getLastMonth() == 876699, "Error LastMonthData"
