from ..level.server import LevelServer
from .common import DBSource

class ServerKVDatabase(DBSource):
    data = LevelServer.extraData

    def getData(self, key):
        return self.data.GetExtraData(key)
    
    def setData(self, key, value):
        self.data.SetExtraData(key, value, autoSave=False)
        self.data.SaveExtraData()

    def removeData(self, key):
        self.data.SetExtraData(key, None)
        self.data.SaveExtraData()

    def clearData(self):
        self.data.CleanExtraData() # type: ignore