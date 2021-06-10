import logging

import urllib, json

_LOGGER = logging.getLogger(__name__)

class gitinformation:
    def __init__(self, repo):
        self._serverName = "https://api.github.com/repos/%s/releases/latest" %(repo)
        self._gitData = None

    def getInformation(self):
        from urllib.request import urlopen
        try:
            myURL = urlopen(self._serverName)
            s = myURL.read()
            dataAnswer = json.loads(s)
        except:
            dataAnswer = {}
        self._gitData = dataAnswer

    def getVersion(self):
        return self._gitData.get("tag_name", "")