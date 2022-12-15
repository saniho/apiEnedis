from __future__ import annotations

import datetime
import json
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class gitinformation:

    _lastUpdates: dict[str, float] = {}
    _lastInfos: dict[str, dict[str, Any]] = {}

    def __init__(self, repo: str):
        self._repo = repo
        self._serverName = f"https://api.github.com/repos/{repo}/releases/latest"
        self._gitData: dict[str, Any]
        if self._repo in gitinformation._lastInfos:
            self._gitData = gitinformation._lastInfos[self._repo]
        else:
            # Ensure the entry exists
            gitinformation._lastInfos[self._repo] = {}

    def getInformation(self) -> None:
        timestamp = datetime.datetime.now().timestamp()
        if (
            self._repo not in gitinformation._lastUpdates
            or gitinformation._lastUpdates[self._repo] < timestamp - 3600
        ):
            gitinformation._lastUpdates[self._repo] = timestamp
            import requests

            try:
                #from urllib.request import urlopen

                #myURL = urlopen(self._serverName)
                #s = myURL.read()

                session = requests.Session()
                response = session.get(
                    self._serverName,
                    timeout=30, )
                #gitinformation._lastInfos[self._repo] = json.loads(s)
                gitinformation._lastInfos[self._repo] = response.json()
                print(1)
            except requests.exceptions.Timeout:
                # a ajouter raison de l'erreur !!!
                _LOGGER.error("requests.exceptions.Timeout")
            except requests.exceptions.HTTPError:
                _LOGGER.error("requests.exceptions.HTTPError : %s"%(response.text))
            except:
                _LOGGER.error(
                        "-- ** retour git en erreur : %s"%(response.text))
                pass

    def getVersion(self) -> str:

        try:
            version = gitinformation._lastInfos[self._repo].get("tag_name", "")
        except:
            version = None

            self._LOGGER.error(
                "-- ** version non disponible : %s", gitinformation._lastInfos[self._repo]
            )
        return version
