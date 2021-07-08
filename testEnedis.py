from custom_components.apiEnedis import myClientEnedis
from custom_components.apiEnedis.sensorEnedis import manageSensorState
import json, datetime
import logging

__version__ = "test_saniho"

from custom_components.apiEnedis.const import (
    _consommation,
    _production,
)

def getLocalDirectory( PDL, dateRepertoire):
    directory = "../myCredential/%s/%s/" %(PDL, dateRepertoire)
    return directory

log = logging.getLogger("testEnedis")

def writeDataJson( myEne ):
    myEne.writeDataJson()

def testMulti():
    logging.basicConfig(level=logging.INFO)
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/security.txt")
    for qui in ["ENEDIS"]:
        log.info("*** traitement de %s " %(qui))
        token = mon_conteneur[qui]['TOKEN']
        PDL_ID = mon_conteneur[qui]['CODE']
        heureCreusesCh = eval("[['00:00','05:00'], ['22:00', '24:00']]")
        heuresCreusesON = True


        # Lecture fichier Json de sortie
        myDataEnedis = myClientEnedis.myClientEnedis( token=token, PDL_ID=PDL_ID, delai=7200,
            heuresCreuses=heureCreusesCh, heuresCreusesCost=0.0797, heuresPleinesCost=0.1175,
            version = __version__, heuresCreusesON=heuresCreusesON )
        path = getLocalDirectory( PDL_ID, "20210631" )
        myDataEnedis.setPathArchive(path)
        dataJson = {}
        dataJson = myDataEnedis.readDataJson()
        myDataEnedis.setDataJsonDefault( dataJsonDefault = dataJson)
        myDataEnedis.setDataJsonCopy()
        myDataEnedis.manageLastCallJson()
        log.info("** on tente une maj ??")
        myDataEnedis.getData()
        log.info("=================< on a fini le call : %s ============" %(myDataEnedis.getNbCall()))

        log.info("" )
        log.info("=================>>>> 2 <<<<============" )
        callPossible = myDataEnedis.getCallPossible()
        log.info("possible ? %s "%(callPossible))
        log.info("** on tente une maj ??")
        myDataEnedis.getData()
        log.info("=================< on a fini le call : %s ============" %(myDataEnedis.getNbCall()))

        log.info("" )
        log.info("=================>>>> 3 <<<<============" )
        callPossible = myDataEnedis.getCallPossible()
        log.info("possible ? %s "%(callPossible))
        log.info("** on tente une maj ??")
        myDataEnedis.getData()
        log.info("=================< on a fini le call : %s ============" %(myDataEnedis.getNbCall()))
        #print(1/0)
        # SORTIE OUTPUT
        writeDataJson( myDataEnedis )

        # ***********************************
        # ***********************************
        myDataSensorEnedis = manageSensorState()
        myDataSensorEnedis.init(myDataEnedis)
        typeSensor = _consommation
        status_counts, state = myDataSensorEnedis.getStatus( typeSensor )
        log.info("****")
        log.info(status_counts)
        for clef in status_counts.keys():
            log.info( "%s = %s" %(clef, status_counts[clef]))

        typeSensor = _production
        status_counts, state = myDataSensorEnedis.getStatus( typeSensor )
        log.info("****")
        log.info(status_counts)
        for clef in status_counts.keys():
            log.info( "%s = %s" %(clef, status_counts[clef]))

        typeSensor = _consommation
        laDate = datetime.datetime.today() - datetime.timedelta(3)
        status_counts, state = myDataSensorEnedis.getStatusHistory( laDate, detail = "ALL" )
        log.info("**** : %s" %state)
        log.info(status_counts)
        for clef in status_counts.keys():
            log.info( "%s = %s" %(clef, status_counts[clef]))

        #laDate = datetime.datetime.today() - datetime.timedelta(2)
        #status_counts, state = myDataSensorEnedis.getStatusHistory(laDate, "ALL")
        #log.info("****")
        #log.info(status_counts, "/", state)


def testMono():
    import configparser
    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../../../myCredential/security.txt")
    qui = "ENEDIS"
    token = mon_conteneur[qui]['TOKEN']
    PDL_ID = mon_conteneur[qui]['CODE']
    log.info(token, PDL_ID)

    heureCreusesCh = "[['00:00','05:00'], ['22:00', '24:00']]"
    myDataEnedis = myClientEnedis.myClientEnedis(token=token, PDL_ID=PDL_ID, delai=10, \
                                       heuresCreuses=eval(heureCreusesCh),
                                       heuresCreusesCost=0.20,
                                       heuresPleinesCost=1.30,
                                       version = __version__)
    myDataEnedis.getData()
    log.info(myDataEnedis.getContract())
    #myDataEnedis.updateProductionYesterday()
    #retour = myDataEnedis.getProductionYesterday()
    #log.info("retour", retour)
    myDataEnedis.updateYesterday()
    retour = myDataEnedis.getYesterday()
    log.info("retour", retour)

def testGitInformation():
    from custom_components.apiEnedis import gitinformation
    git = gitinformation.gitinformation( "saniho/apiEnedis" )
    git.getInformation()
    log.info(git.getVersion())

def main():
    testMulti()
    testGitInformation()
    #testMono()

if __name__ == '__main__':
    main()
""" get all update and charge l'instance et utilisation avec get after ....."""