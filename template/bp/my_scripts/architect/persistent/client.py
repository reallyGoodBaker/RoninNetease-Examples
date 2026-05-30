from ..conf import DB_GLOBAL_NAME, DB_NAME
from ..level.client import LevelClient
from .common import DBSource


class ClientKVDatabase(DBSource):

    def __init__(self):
        self.conf = LevelClient.getInstance().configClient
        self.data = self.conf.GetConfigData(DB_NAME)

    def getData(self, key):
        return self.data.get(key)
    
    def _save(self):
        self.conf.SetConfigData(DB_NAME, self.data)
    
    def setData(self, key, value):
        self.data[key] = value
        self._save()

    def removeData(self, key):
        self.data.pop(key)
        self._save()

    def clearData(self):
        self.data = {}
        self._save()


class ClientKVDatabaseGlobal(DBSource):

    def __init__(self):
        self.conf = LevelClient.getInstance().configClient
        self.data = self.conf.GetConfigData(DB_GLOBAL_NAME, True)

    def getData(self, key):
        return self.data.get(key)
    
    def _save(self):
        self.conf.SetConfigData(DB_GLOBAL_NAME, self.data, True)
    
    def setData(self, key, value):
        self.data[key] = value
        self._save()

    def removeData(self, key):
        self.data.pop(key)
        self._save()

    def clearData(self):
        self.data = {}
        self._save()