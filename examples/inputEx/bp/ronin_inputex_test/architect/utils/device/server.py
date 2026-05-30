from ...core.basic import serverApi

class deviceServer:
    @staticmethod
    def mcVer():
        return serverApi.GetMinecraftVersion()
    
    @staticmethod
    def platform():
        return serverApi.GetPlatform()
    
    @staticmethod
    def inApollo():
        return serverApi.IsInApollo()
    
    @staticmethod
    def inServer():
        return serverApi.IsInServer()