#!/usr/bin/env python3.8
from __future__ import annotations

import ast
import logging
from typing import Any

from custom_components.apiEnedis import myClientEnedis
from custom_components.apiEnedis.const import _consommation, _production
from custom_components.apiEnedis.sensorEnedis import manageSensorState

LOGGER = logging.getLogger("testEnedis")
LOGGER.setLevel(
    logging.DEBUG
)  # Aide au debogue, à définir avant le chargement du reste


__version__ = "test_saniho"


myClientEnedis.log.setLevel(logging.DEBUG)  # Aide au debogue


def getLocalDirectory(PDL, dateRepertoire):
    directory = f"../myCredential/{PDL}/{dateRepertoire}/"
    return directory


def writeDataJson(myEne):
    myEne.writeDataJson()


def testMulti():
    logging.basicConfig(level=logging.INFO)
    import configparser

    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../myCredential/security.txt")
    for qui in ["ENEDIS100"]:
        LOGGER.info(f"*** traitement de {qui} ")
        token = mon_conteneur[qui]["TOKEN"]
        PDL_ID = mon_conteneur[qui]["CODE"]
        serviceEnedis = "enedisGateway"
        if "SERVICE" in mon_conteneur[qui].keys():
            serviceEnedis = mon_conteneur[qui]["SERVICE"]

        print(mon_conteneur[qui]["QUI"], serviceEnedis)
        heureCreusesCh = ast.literal_eval("[['00:00','05:00'], ['22:00', '24:00']]")
        heuresCreusesON = True

        # Lecture fichier Json de sortie
        myDataEnedis = myClientEnedis.myClientEnedis(
            token=token,
            PDL_ID=PDL_ID,
            delay=7200,
            heuresCreuses=heureCreusesCh,
            heuresCreusesCost=0.0797,
            heuresPleinesCost=0.1175,
            version=__version__,
            heuresCreusesON=heuresCreusesON,
            serviceEnedis=serviceEnedis
        )
        path = getLocalDirectory(PDL_ID, "20220308")
        LOGGER.info("Archive path: '%s'", path)
        myDataEnedis.setPathArchive(path)
        dataJson: dict[str, Any] = {}
        # dataJson = myDataEnedis.readDataJson()
        myDataEnedis.setDataJsonDefault(dataJsonDefault=dataJson)
        myDataEnedis.setDataJsonCopy()
        myDataEnedis.manageLastCallJson()
        LOGGER.info("** on tente une maj ??")
        myDataEnedis.getData()
        LOGGER.info(
            "=================< on a fini le call : %s ============",
            myDataEnedis.getNbCall(),
        )

        # LOGGER.info("" )
        LOGGER.info("=================>>>> 2 <<<<============")
        # time = datetime.datetime.now() + datetime.timedelta(hours=1)
        callPossible = myDataEnedis.getCallPossible()
        LOGGER.info(f"possible ? {callPossible} ")
        LOGGER.info("** on tente une maj ??")
        myDataEnedis.getData()
        LOGGER.info(
            "=================< on a fini le call : %s ============",
            myDataEnedis.getNbCall(),
        )

        # SORTIE OUTPUT
        # writeDataJson(myDataEnedis)

        # ***********************************
        # ***********************************
        myDataSensorEnedis = manageSensorState()
        myDataSensorEnedis.init(myDataEnedis)
        typeSensor = _consommation
        status_counts, state = myDataSensorEnedis.getStatus(typeSensor)
        typeSensor = _production
        status_counts, state = myDataSensorEnedis.getStatus(typeSensor)
        # lastReset, status_counts, state = (
        #         myDataSensorEnedis.getStatusEnergyDetailHours( typeSensor )
        #     )
        # lastReset, status_counts, state = (
        #         myDataSensorEnedis.getStatusEnergyDetailHoursCost( typeSensor )
        #     )
        LOGGER.info("****")
        LOGGER.info(status_counts)
        for clef in status_counts.keys():
            LOGGER.info(f"{clef} = {status_counts[clef]}")
        #
        # typeSensor = _production
        # status_counts, state = myDataSensorEnedis.getStatus( typeSensor )
        # LOGGER.info("****")
        # LOGGER.info(status_counts)
        # for clef in status_counts.keys():
        #     LOGGER.info( "%s = %s" %(clef, status_counts[clef]))
        #
        # typeSensor = _consommation
        # laDate = datetime.datetime.today() - datetime.timedelta(3)
        # status_counts, state = (
        #     myDataSensorEnedis.getStatusHistory( laDate, detail = "ALL" )
        # )
        # LOGGER.info("**** : %s" %state)
        # LOGGER.info(status_counts)
        # for clef in status_counts.keys():
        #     LOGGER.info( "%s = %s" %(clef, status_counts[clef]))

        # laDate = datetime.datetime.today() - datetime.timedelta(2)
        # status_counts, state = myDataSensorEnedis.getStatusHistory(laDate, "ALL")
        # LOGGER.info("****")
        # LOGGER.info(status_counts, "/", state)


def testMono():
    import configparser

    mon_conteneur = configparser.ConfigParser()
    mon_conteneur.read("../../../myCredential/security.txt")
    qui = "ENEDIS"
    token = mon_conteneur[qui]["TOKEN"]
    PDL_ID = mon_conteneur[qui]["CODE"]
    LOGGER.info("TOken: '%s', PDL_ID: '%s'", token, PDL_ID)

    heureCreusesCh = "[['00:00','05:00'], ['22:00', '24:00']]"
    myDataEnedis = myClientEnedis.myClientEnedis(
        token=token,
        PDL_ID=PDL_ID,
        delay=10,
        heuresCreuses=ast.literal_eval(heureCreusesCh),
        heuresCreusesCost=0.20,
        heuresPleinesCost=1.30,
        version=__version__,
    )
    myDataEnedis.getData()
    LOGGER.info(myDataEnedis.contract)
    # myDataEnedis.updateProductionYesterday()
    # retour = myDataEnedis.getProductionYesterday()
    # LOGGER.info("retour %s", retour)
    myDataEnedis.updateYesterday()
    retour = myDataEnedis.getYesterday()
    LOGGER.info("retour %s", retour)


def main():
    testMulti()
    # testMono()


if __name__ == "__main__":
    """get all update and charge l'instance et utilisation avec get after ....."""
    main()
