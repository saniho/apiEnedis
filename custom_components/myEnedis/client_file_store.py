"""File I/O for JSON persistence - no HA dependency."""
from __future__ import annotations

import glob
import json
import logging
import os

from . import apiconst as API
from .const import __nameMyEnedis__

log = logging.getLogger(__nameMyEnedis__)


class FileStore:
    def __init__(self, path: str | None, pdl_id: str):
        self._path = path
        self._pdl_id = pdl_id

    def read_all(self) -> dict:
        data = {}
        data_repertoire = self._path
        log.info("fichier lu dataRepertoire : %s", data_repertoire)
        if data_repertoire is None:
            return data
        directory = f"{data_repertoire}/*.json"
        log.info("fichier lu directory : %s", directory)
        liste_file = glob.glob(directory)
        log.info("fichier lu listeFile : %s", liste_file)
        for nom_fichier in liste_file:
            try:
                with open(nom_fichier) as json_file:
                    clef = os.path.basename(nom_fichier).split(".")[0]
                    data[clef] = json.load(json_file)
            except Exception:
                log.error(">>>> erreur lecture : %s", nom_fichier)
        return data

    def write_all(self, data: dict) -> None:
        if self._path is None or not data:
            return
        for clef, value in data.items():
            try:
                nom_fichier = f"{self._path}/{clef}.json"
                ne_pas_ecrire = False
                if API.ENEDIS_RETURN in value:
                    enedis_return = value[API.ENEDIS_RETURN]
                    if API.ENEDIS_RETURN_ERROR in enedis_return:
                        ne_pas_ecrire = enedis_return[API.ENEDIS_RETURN_ERROR] in (
                            "UNKERROR_TIMEOUT",
                            "UNAVAILABLE",
                        )
                log.info(">>>> ecriture : %s / %s", nom_fichier, value)
                if not ne_pas_ecrire:
                    with open(nom_fichier, "w") as outfile:
                        json.dump(value, outfile)
            except Exception:
                log.error(">>>> erreur ecriture : %s", nom_fichier)
