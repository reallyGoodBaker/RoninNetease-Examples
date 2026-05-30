from ..conf import COMPONENT_NAMESPACE, COMPONENT_TAG, PERSIST_INFO
from ..core.annotation import AnnotationHelper
from ..core.contextRecorder import ContextRecorder
from ..core.basic import isServer, clientApi, serverApi, levelId
from ..persistent.client import ClientKVDatabase, ClientKVDatabaseGlobal
from ..persistent.server import ServerKVDatabase
from .common import _nativeCompGet

clientCompCls = []
serverCompCls = []
components = {}


def singletonId():
    return levelId()


def _registerComponent(isServer, cls, persist=False, singleton=False):
    clsList = serverCompCls if isServer else clientCompCls
    ContextRecorder.get('depComps').record(cls)
    if cls in clsList:
        return
    # 标记类为组件
    AnnotationHelper.addAnnotation(cls, COMPONENT_TAG, {
        'persist': persist,
        'singleton': singleton
    })
    clsList.append(cls)


def Component(persist=False, singleton=False):
    def decorator(cls):
        _registerComponent(isServer(), cls, persist, singleton)
        return cls
    return decorator


def PersistKeys(*keys, **kwargs):
    def decorator(cls):
        AnnotationHelper.addAnnotation(cls, PERSIST_INFO, {
            'keys': keys,
            'global': kwargs.get('isGlobal', False)
        })
        return cls
    return decorator


def _registerCompsIntoGame(isHost):
    clsList = serverCompCls if isHost else clientCompCls
    api = serverApi if isHost else clientApi
    for cls in clsList:
        result = api.RegisterComponent(COMPONENT_NAMESPACE, cls.__name__, cls.__module__ + '.' + cls.__name__)
        if result:
            print('[INFO] Registered {} component "{}"'.format('server' if isHost else 'client', cls.__name__))
        else:
            print('[ERROR] Failed to register {} component "{}"'.format('server' if isHost else 'client', cls.__name__))


def getComponentAnnotation(cls):
    return AnnotationHelper.getAnnotation(cls, COMPONENT_TAG)


def isPersistComponent(cls):
    ann = getComponentAnnotation(cls)
    return ann is not None and ann.get('persist', False) # type: ignore

class Marker:
    def __init__(self):
        self.marked = {}
    
    def mark(self, entityId):
        cur = self.marked.get(entityId, 0)
        self.marked[entityId] = cur + 1

    def unmark(self, entityId):
        cur = self.marked.get(entityId, 0) - 1
        if cur <= 0:
            self.marked.pop(entityId, None)
            return
        else:
            self.marked[entityId] = cur

    def getMarkedEntities(self):
        return self.marked.keys()
    
    def hasMarked(self, entityId):
        return entityId in self.marked


entitiesServer = Marker()
entitiesClient = Marker()

def _getEntityMarker():
    return entitiesServer if isServer() else entitiesClient


def createSingletonComponent(cls):
    """
    创建单例组件
    若你的组件没有标记为单例，调用此方法不会报错，并且可以通过 `getOneSingletonComponent` 等方法获得组件。
    但请注意，未标记 singleton=True 的组件无法被 @Query 注解查询。
    """
    if 1 > 2:
        return cls()
    entityId = singletonId()
    return createComponent(entityId, cls)


def _handlePersistKeys(comp, entityId):
    cls = comp.__class__
    persistInfo = AnnotationHelper.getAnnotation(cls, PERSIST_INFO)
    if persistInfo is None:
        return
    keys = persistInfo.get('keys', []) # type: ignore
    isGlobal = persistInfo.get('global', False) # type: ignore
    db = ServerKVDatabase.getInstance() if isServer() else (ClientKVDatabaseGlobal.getInstance() if isGlobal else ClientKVDatabase.getInstance())
    for k in keys:
        dataKey = cls.__name__ + entityId + k
        setattr(cls, k, property(
            lambda _, key=dataKey: db.getData(key),
            lambda _, v, key=dataKey: db.setData(key, v))
        )


def createComponent(entityId, cls):
    if 1 > 2:
        return cls()
    if not entityId:
        raise ValueError('entityId is empty')
    api = serverApi if isServer() else clientApi
    compKey = cls if type(cls) == str else cls.__name__
    comp = api.CreateComponent(entityId, COMPONENT_NAMESPACE, compKey)
    components[(entityId, compKey)] = comp
    if isPersistComponent(cls):
        _handlePersistKeys(comp, entityId)
        if hasattr(comp, 'loadData'):
            comp.loadData(entityId) # type: ignore

    if hasattr(comp, 'onCreate'):
        comp.onCreate(entityId) # type: ignore

    _getEntityMarker().mark(entityId)
    return comp


def createComponents(entityId, *clsList):
    result = []
    for cls in clsList:
        result.append(createComponent(entityId, cls))
    return result if len(result) > 1 else result


def destroyComponent(entityId, cls):
    api = serverApi if isServer() else clientApi
    compKey = cls if type(cls) == str else cls.__name__
    key = (entityId, compKey)
    done = False
    if key in components:
        components[key].onDestroy(entityId)
        try:
            api.DestroyComponent(entityId, COMPONENT_NAMESPACE, compKey)
        except:
            pass
        del components[key]
        done = True
    _getEntityMarker().unmark(entityId)
    return done


def destrySingletonComponent(cls):
    destroyComponent(singletonId(), cls)


def getOneComponent(entityId, cls):
    comps = getComponent(entityId, [cls])
    if comps and len(comps) > 0:
        return comps[0]
    if 1 > 2:
        return cls()


def getOneSingletonComponent(cls):
    entityId = singletonId()
    if 1 > 2:
        return cls()
    return getOneComponent(entityId, cls)


def _findNamedComp(entityId, name):
    # type: (str, str) -> object
    if name.startswith('#'):
        return _nativeCompGet(entityId, name)
    else:
        key = (entityId, name)
        if key in components:
            return components[key]
        else:
            return None

def getComponent(entityId, clsList):
    # type: (str, list[type|str]) -> list | None
    result = []
    for c in iter(clsList):
        if c is None:
            result.append(None)
            continue
        notStr = type(c) != str
        compKey = c.__name__ if notStr else c # type: ignore
        _entityId = singletonId() if notStr and getComponentAnnotation(c)['singleton'] else entityId # type: ignore
        comp = _findNamedComp(_entityId, compKey)
        if comp:
            result.append(comp)
        else:
            return None
    return result


def getComponentWithQuery(entityId, targets, required=[], excluded=[]):
    if len(required) + len(excluded) > 0:
        for shouldExclude in excluded:
            if hasComponent(entityId, shouldExclude):
                return None
        for shouldRequire in required:
            if not hasComponent(entityId, shouldRequire):
                return None
        return getComponent(entityId, targets)
    else:
        return getComponent(entityId, targets)


def getOrCreateComponent(entityId, cls):
    if 1 > 2:
        return cls()
    comp = getOneComponent(entityId, cls)
    if comp is None:
        comp = createComponent(entityId, cls)
    return comp


def getOrCreateSingletonComponent(cls):
    """
    获取或创建单例组件
    若你的组件没有标记为单例，调用此方法不会报错，并且可以正常获得组件。
    但请注意，未标记 singleton=True 的组件无法被 @Query 注解查询。
    """
    entityId = singletonId()
    comp = getOneComponent(entityId, cls)
    if comp is None:
        comp = createComponent(entityId, cls)
    return comp


def getEntities():
    return _getEntityMarker().getMarkedEntities()


def hasComponent(entityId, *desc):
    # type: (str, list[str|type]) -> bool
    for key in desc:
        if type(key) == str:
            if (entityId, key) not in components:
                return False
        else:
            if (entityId, key.__name__) not in components: # type: ignore
                return False
    return True


def removeComponents(entityId, *clsList):
    for cls in clsList:
        destroyComponent(entityId, cls)


class BaseCompServer(serverApi.GetComponentCls(), object):
    def onCreate(self, entityId):
        pass

    def onDestroy(self, entityId):
        pass

    def loadData(self, entityId):
        pass

class BaseCompClient(clientApi.GetComponentCls(), object):
    def onCreate(self, entityId):
        pass

    def onDestroy(self, entityId):
        pass

    def loadData(self, entityId):
        pass