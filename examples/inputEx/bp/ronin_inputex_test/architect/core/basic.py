import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
import threading

class Location:
    def __init__(self, pos, dim):
        self.pos = pos
        self.dim = dim

__threads = {}
__meta = {}

def isServer():
    curId = threading.current_thread().ident
    if curId in __threads:
        return __threads[curId]
    else:
        localPlayerId = clientApi.GetLocalPlayerId()
        _isServer = localPlayerId == '-1'
        if not _isServer:
            __meta['localPlayerId'] = localPlayerId
        __threads[threading.current_thread().ident] = _isServer
        return _isServer

def levelId():
    if isServer():
        if __meta.get('levelIdServer', None) is None:
            __meta['levelIdServer'] = serverApi.GetLevelId()
        return __meta['levelIdServer']
    else:
        if __meta.get('levelIdClient', None) is None:
            __meta['levelIdClient'] = clientApi.GetLevelId()
        return __meta['levelIdClient']

localPlayerId = lambda: __meta.get('localPlayerId', '-1') # 不要在服务器端使用

def getComponentCls():
    if isServer():
        return serverApi.GetComponentCls()
    else:
        return clientApi.GetComponentCls()

def getGoalCls():
    return serverApi.GetCustomGoalCls()

def serverTick():
    return serverApi.GetServerTickTime()

compServer = serverApi.GetEngineCompFactory()
compClient = clientApi.GetEngineCompFactory()

defaultFilters = {
    "any_of": [
        {
            "subject" : "other",
            "test" :  "is_family",
            "value" :  "player"
        },
        {
            "subject" : "other",
            "test" :  "is_family",
            "value" :  "mob"
        }
    ]
}