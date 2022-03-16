from __future__ import annotations

import json
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class gitinformation:
    def __init__(self, repo: str):
        self._serverName = f"https://api.github.com/repos/{repo}/releases/latest"
        self._gitData: dict[str, Any]

    def getInformation(self) -> None:
        from urllib.request import urlopen

        try:
            myURL = urlopen(self._serverName)
            s = myURL.read()
            dataAnswer = json.loads(s)
        except:
            dataAnswer = {}
        self._gitData = dataAnswer

    def getVersion(self) -> str:
        return self._gitData.get("tag_name", "")
