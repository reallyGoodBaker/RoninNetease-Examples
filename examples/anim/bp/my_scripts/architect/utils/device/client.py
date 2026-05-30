from ...core.basic import clientApi, compClient

class deviceClient:

    @staticmethod
    def engineVer():
        return clientApi.GetEngineVersion()
    
    @staticmethod
    def ip():
        return clientApi.GetIP()

    @staticmethod
    def mcVer():
        return clientApi.GetMinecraftVersion()

    @staticmethod
    def platform():
        return clientApi.GetPlatform()
    
    @staticmethod
    def fps():
        return compClient.CreateGame(clientApi.GetLevelId())