from custom_components.apiEnedis import myClientEnedis
from custom_components.apiEnedis.sensorEnedis import manageSensorState
import json, datetime
import logging

__version__ = "test_saniho"

from custom_components.apiEnedis.const import (
    _consommation,
    _production,
)

dateRepertoire = "20210617"
directory = "../myCredential/%s/" %(dateRepertoire)

def writeDataJson( myEne ):
    myEne.writeDataJson()

def readDataJson( myEne):
    myEne.setPathArchive(directory)
    data = myEne.readDataJson()
    myEne.setDataJsonDefault( dataJsonDefault=data )
    myEne.setDataJsonCopy()
    myEne.manageLastCallJson()
    return data

def testMulti():
    #logging.basicConfig(level=logging.INFO)
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/security.txt")
    for qui in ["ENEDIS"]:
        print("*** traitement de %s " %(qui))
        token = mon_conteneur[qui]['TOKEN']
        PDL_ID = mon_conteneur[qui]['CODE']
        heureCreusesCh = eval("[['00:00','05:00'], ['22:00', '24:00']]")
        heuresCreusesON = True

        # Lecture fichier Json de sortie
        myDataEnedis = myClientEnedis.myClientEnedis( token=token, PDL_ID=PDL_ID, delai=7200,
            heuresCreuses=heureCreusesCh, heuresCreusesCost=0.0797, heuresPleinesCost=0.1175,
            version = __version__, heuresCreusesON=heuresCreusesON )
        dataJson = readDataJson(myDataEnedis)
        #dataJson = {}
        myDataEnedis.setDataJsonDefault( dataJsonDefault = dataJson)
        print("** on tente une maj ??")
        myDataEnedis.getData()
        print("===< on a fini le call : %s" %(myDataEnedis.getNbCall()))
        callPossible = myDataEnedis.getCallPossible()
        print("possible ? %s "%(callPossible))
        print("** on tente une maj ??")
        myDataEnedis.getData()
        print("===< on a fini le call : %s" %(myDataEnedis.getNbCall()))
        #currentDateTime = (datetime.datetime.now() + datetime.timedelta(hours=1))
        #callPossible = myDataEnedis.getCallPossible(currentDateTime)
        #print("possible %s ? %s "%(currentDateTime, callPossible))
        #currentDateTime = (datetime.datetime.now() + datetime.timedelta(hours=5))
        #callPossible = myDataEnedis.getCallPossible(currentDateTime)
        #print("possible %s ? %s "%(currentDateTime, callPossible))
        #currentDateTime = (datetime.datetime.now() + datetime.timedelta(days=1))
        #callPossible = myDataEnedis.getCallPossible(currentDateTime)
        #print("possible %s ? %s "%(currentDateTime, callPossible))
        #print("myDataEnedis.getContract() : ", myDataEnedis.getContract())
        #print("myDataEnedis.getContract() : ", myDataEnedis.getContract().getUsagePointStatus())
        #print("myDataEnedis.getContract() : ", myDataEnedis.getContract().getTypePDL())
        #print("myDataEnedis.getLastActivationDate() : ", myDataEnedis.getContract().getLastActivationDate())
        #print("myDataEnedis.getHeuresCreuses() : ", myDataEnedis.getContract().getHeuresCreuses())

        #print("consommation : %s" %myDataEnedis.getYesterday().getValue() )

        # SORTIE OUTPUT
        writeDataJson( myDataEnedis )

        # ***********************************
        # ***********************************
        myDataSensorEnedis = manageSensorState()
        myDataSensorEnedis.init(myDataEnedis)
        typeSensor = _consommation
        status_counts, state = myDataSensorEnedis.getStatus( typeSensor )
        print("****")
        print(status_counts)
        for clef in status_counts.keys():
            print( "%s = %s" %(clef, status_counts[clef]))

        typeSensor = _production
        status_counts, state = myDataSensorEnedis.getStatus( typeSensor )
        print("****")
        print(status_counts)
        for clef in status_counts.keys():
            print( "%s = %s" %(clef, status_counts[clef]))

        typeSensor = _consommation
        laDate = datetime.datetime.today() - datetime.timedelta(3)
        status_counts, state = myDataSensorEnedis.getStatusHistory( laDate, detail = "ALL" )
        print("**** : ", state)
        print(status_counts)
        for clef in status_counts.keys():
            print( "%s = %s" %(clef, status_counts[clef]))

        #laDate = datetime.datetime.today() - datetime.timedelta(2)
        #status_counts, state = myDataSensorEnedis.getStatusHistory(laDate, "ALL")
        #print("****")
        #print(status_counts, "/", state)


def testMono():
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../../../myCredential/security.txt")
    qui = "ENEDIS"
    token = mon_conteneur[qui]['TOKEN']
    PDL_ID = mon_conteneur[qui]['CODE']
    print(token, PDL_ID)

    heureCreusesCh = "[['00:00','05:00'], ['22:00', '24:00']]"
    myDataEnedis = myClientEnedis.myClientEnedis(token=token, PDL_ID=PDL_ID, delai=10, \
                                       heuresCreuses=eval(heureCreusesCh),
                                       heuresCreusesCost=0.20,
                                       heuresPleinesCost=1.30,
                                       version = __version__)
    myDataEnedis.getData()
    print(myDataEnedis.getContract())
    #myDataEnedis.updateProductionYesterday()
    #retour = myDataEnedis.getProductionYesterday()
    #print("retour", retour)
    myDataEnedis.updateYesterday()
    retour = myDataEnedis.getYesterday()
    print("retour", retour)

def testGitInformation():
    from custom_components.apiEnedis import gitinformation
    git = gitinformation.gitinformation( "saniho/apiEnedis" )
    git.getInformation()
    print(git.getVersion())

def main():
    testMulti()
    testGitInformation()
    #testMono()

if __name__ == '__main__':
    main()
""" get all update and charge l'instance et utilisation avec get after ....."""