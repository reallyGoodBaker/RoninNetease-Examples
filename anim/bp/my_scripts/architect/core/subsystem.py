import time

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi

from .annotation import AnnotationHelper
from .scheduler import Scheduler, Sched, SimpleFixedScheduler
from .basic import isServer, Location
from .configurator import modConf, __modname__

from ..component.core import _registerCompsIntoGame, getOrCreateSingletonComponent
from ..event.core import EventSignal
from ..event.client import event as eventClient
from ..event.server import event as eventServer
from ..conf import EVENT_LISTENER, CUSTOM_EVENT, SYSTEM_SCHED_ANNO, SCHED_EVENT

from .typeHelper import castTo


class EventListener:
    def __init__(self, evType, fn):
        self.evType = evType
        self.fn = fn
        setattr(self, fn.__name__, self.fn)


class SubsystemManager(object):
    @staticmethod
    def _relative(path):
        # type: (str) -> str
        return __modname__ + '.' + path


    @staticmethod
    def getInstance():
        # type: () -> SubsystemManager
        """
        可以放心调用，因为具体实现逻辑不在 SubsystemManager 内部
        """
        pass


    def createClient(self):
        # 在manager之前初始化，否则无法监听组件注册和子系统变更
        self.rawEngine = clientApi.GetEngineNamespace()
        self.rawSysName = clientApi.GetEngineSystemName()
        self._initManager(False)
        return self


    def createServer(self):
        self.rawEngine = serverApi.GetEngineNamespace()
        self.rawSysName = serverApi.GetEngineSystemName()
        listener = EventListener('LoadServerAddonScriptsAfter', lambda _: self._initManager(True))
        self.system.ListenForEvent(
            self.rawEngine,
            self.rawSysName,
            'LoadServerAddonScriptsAfter',
            listener,
            listener.fn # type: ignore
        )
        return self


    def __init__(self, system, engine, sysName):
        self.engine = engine
        self.sysName = sysName
        self.system = system
        self._preloaded = False
        self.INITIALIZED = EventSignal()
        self.PRELOADED = EventSignal()
        self.registeredSubsystems = []
        self.rawEngine = None
        self.rawSysName = None
        self.subsystems = {}
        self.listeners = []
        self.renderSched = Scheduler()
        self.tickSched = Scheduler()
        from ..remote.common import _registerRemoteCalls
        _registerRemoteCalls(self)


    def _record(self, inst):
        self.subsystems[inst.__class__.__name__] = inst


    def _removeRecord(self, inst):
        self.subsystems.pop(inst.__class__.__name__, None)


    def _addAnnotatedSubsystems(self):
        for subsystemCls in self.registeredSubsystems:
            self.addSubsystem(subsystemCls)
        self.unregisterSubsystems()


    def _importModules(self, isHost):
        getConf = modConf()
        for module in getConf('MOD_{}_MODULES'.format('SERVER' if isHost else 'CLIENT')): # type: ignore
            importer = serverApi if isHost else clientApi
            importer.ImportModule(self._relative(module))


    def _initManager(self, isHost):
        self._importModules(isHost)
        self.INITIALIZED.emit()
        self._preloaded = True
        _registerCompsIntoGame(isHost)
        self._addAnnotatedSubsystems()
        self._callReady(isHost)
        self.startTicking(isHost)


    def _callReady(self, isServer):
        subs = self.subsystems
        for v in subs.values():
            v.onReady()
        self.PRELOADED.emit()


    def startTicking(self, isServer):
        if isServer:
            self.system.ListenForEvent(
                self.rawEngine,
                self.rawSysName,
                'OnScriptTickServer',
                self,
                self.tickSubsystem
            )
        else:
            self.system.ListenForEvent(
                self.rawEngine,
                self.rawSysName,
                'OnScriptTickClient',
                self,
                self.tickSubsystem
            )
            self.system.ListenForEvent(
                self.rawEngine,
                self.rawSysName,
                'GameRenderTickEvent',
                self,
                self.tickRender
            )


    def addSubsystem(self, subsystemCls):
        subSys = subsystemCls(self.system, self.engine, self.sysName)
        subSys._init()
        print('[INFO] {} Subsystem "{}" has been initialized'.format('Server' if isServer() else 'Client', subSys.__class__.__name__))


    def getSubsystem(self, subsystemCls):
        # type: (object) -> 'Subsystem'
        return self.subsystems.get(subsystemCls if type(subsystemCls) is str else subsystemCls.__name__) # type: ignore


    def getSubsystemByName(self, name):
        # type: (str) -> 'Subsystem'
        return self.subsystems.get(name) # type: ignore


    def removeSubsystem(self, subsystemCls):
        subSystems = self.subsystems
        subSys = subSystems[subsystemCls.__name__]
        subSys._destroy()


    def registerSubsystem(self, subsystem):
        if not self._preloaded:
            self.registeredSubsystems.append(subsystem)
        else:
            self.addSubsystem(subsystem)


    def unregisterSubsystems(self):
        self.registeredSubsystems = []


    lastTickTimeServer = time.time()
    lastTickTime = time.time()
    lastFrameTime = time.time()

    def tickSubsystem(self):
        currentTime = time.time()
        dt = currentTime - self.lastTickTimeServer

        for obj in self.subsystems.values():
            if obj.canTick:
                obj.onUpdate(dt)
                obj.ticks += 1

        self.lastTickTimeServer = currentTime
        self.tickSched.executeSequence()


    def tickRender(self, _):
        currentTime = time.time()
        dt = max(1e-5, currentTime - self.lastFrameTime)
        self.lastFrameTime = currentTime

        for obj in self.subsystems.values():
            if obj.canTick:
                obj.onRender(dt)

        self.renderSched.executeSequence()


    def addListener(self, event, fn, isCustomEvent=False):
        listeners = self.listeners
        listener = EventListener(event, fn)
        if isCustomEvent:
            self.system.ListenForEvent(
                self.engine,
                self.sysName,
                event,
                listener,
                listener.fn
            )
        else:
            self.system.ListenForEvent(
                self.rawEngine,
                self.rawSysName,
                event,
                listener,
                listener.fn
            )
        listeners.append(listener)


    def removeListener(self, event, fn):
        listeners = self.listeners
        for listener in listeners:
            if listener.fn == fn:
                self.system.UnListenForEvent(
                    self.rawEngine,
                    self.rawSysName,
                    event,
                    listener,
                    listener.fn
                )
                listeners.remove(listener)


class Subsystem(object):
    def __init__(self, system, engine, sysName):
        # type: (_ShadowSystemServer | _ShadowSystemClient, str, str) -> 'None'
        self.system = system        # type: _ShadowSystemServer | _ShadowSystemClient
        self.engine = engine        # type: str
        self.sysName = sysName      # type: str
        self.ticks = 0              # type: int
        self.canTick = False        # type: bool
        self.initialized = False    # type: bool

    def onUpdate(self, dt):
        """
        每tick调用

        需要设置 `canTick` 为 `True`
        """
        pass

    def onReady(self):
        """
        所有子系统初始化完毕后调用

        此时所有子系统已经创建完毕，可以通过 `getSubsystem` 获取其他子系统
        """
        pass

    def onInit(self):
        """
        当前子系统创建完毕后调用

        此时 `SubystemManager` 已经创建完毕
        """
        pass

    def onDestroy(self):
        pass

    @classmethod
    def getInstance(cls):
        if 1 > 2:
            return cls() # type: ignore
        return SubsystemManager.getInstance().getSubsystem(cls) # type: ignore

    def getHost(self):
        # type: () -> _ShadowSystemServer | _ShadowSystemClient
        return self.system
    
    def getEngine(self):
        # type: () -> str
        return self.engine
    
    def getSysName(self):
        # type: () -> str
        return self.sysName
    
    def on(self, eventName, handler, isCustomEvent=True):
        # type: (str, function, bool) -> None
        return self._addListener(eventName, handler, isCustomEvent)

    def off(self, eventName, handler, isCustomEvent=True):
        # type: (str, function, bool) -> None
        return self._removeListener(eventName, handler, isCustomEvent)

    def listen(self, eventName, handler):
        # type: (str, function) -> None
        return self._addListener(eventName, handler, False)

    def unlisten(self, eventName, handler):
        # type: (str, function) -> None
        return self._removeListener(eventName, handler, False)

    def broadcast(self, eventName, eventData):
        # type: (str, dict) -> None
        self.system.BroadcastEvent(eventName, eventData)

    def _addListener(self, eventType, fn, isCustom=False):
        event = eventServer if isServer() else eventClient
        event(eventType, isCustom).addListener(fn)

    def _removeListener(self, eventType, fn, isCustom=False):
        event = eventServer if isServer() else eventClient
        event(eventType, isCustom).removeListener(fn)

    def _removeListeners(self):
        methods = AnnotationHelper.findAnnotatedMethods(self, EVENT_LISTENER)
        for method in methods:
            eventType = AnnotationHelper.getAnnotation(method, EVENT_LISTENER)
            isCustomEvent = AnnotationHelper.getAnnotation(method, CUSTOM_EVENT) or False
            instMethod = method.__get__(self)
            self._removeListener(eventType, instMethod, isCustomEvent) # type: ignore

    def _addListeners(self):
        methods = AnnotationHelper.findAnnotatedMethods(self, EVENT_LISTENER)
        for method in methods:
            eventType = AnnotationHelper.getAnnotation(method, EVENT_LISTENER)
            isCustomEvent = AnnotationHelper.getAnnotation(method, CUSTOM_EVENT) or False
            instMethod = method.__get__(self)
            self._addListener(eventType, instMethod, isCustomEvent) # type: ignore

    def _addSchedMethods(self):
        methods = AnnotationHelper.findAnnotatedMethods(self, SYSTEM_SCHED_ANNO)
        for method in methods:
            schedType, schedFlag, opt = castTo(AnnotationHelper.getAnnotation(method, SYSTEM_SCHED_ANNO), tuple, str, str, dict)
            instMethod = method.__get__(self)
            _isServer = isServer()
            manager = SubsystemManager.getInstance()
            if schedType == Sched.TYPE_RENDER:
                if _isServer:
                    continue
                manager.renderSched.addTask(schedFlag, instMethod)
            elif schedType == Sched.TYPE_TICK:
                sched = manager.tickSched
                sched.addTask(schedFlag, instMethod)
            elif schedType == Sched.TYPE_FIXED:
                schedulerName = opt['schedulerName']
                sched = self._addFixedSched(schedulerName, schedFlag, instMethod)
            elif schedType == Sched.TYPE_EVENT:
                isCustom = opt.get('isCustom')
                eventType = opt.get('eventType')
                self._handleSchedEvents(eventType, instMethod, isCustom, schedFlag)

    def _handleSchedEvents(self, eventType, instMethod, isCustom, schedFlag):
        schedKey = (eventType, isCustom)
        reader = getOrCreateSingletonComponent('EventReader')
        if not reader:
            return
        if schedKey not in self._schedEvents:
            schedListeners = ([], []) # type: tuple[list[function], list[function]]
            self._schedEvents[schedKey] = schedListeners
            def handler(event):
                reader.ev = event # type: ignore
                for stage in self._schedEvents[schedKey]:
                    for fn in stage:
                        fn()  # type: ignore
                reader.ev = None  # type: ignore
            self.on(eventType, handler, isCustom)  # type: ignore
        schedListeners = self._schedEvents[schedKey]
        targetList = schedListeners[0] if schedFlag == SCHED_EVENT else schedListeners[1]
        targetList.append(instMethod)

    def _removeSchedEvents(self):
        for schedKey, schedList in self._schedEvents.items():
            eventType, isCustom = schedKey
            for fn in schedList:
                self.off(eventType, fn, isCustom) # type: ignore

    def _removeSchedMethods(self):
        methods = AnnotationHelper.findAnnotatedMethods(self, SYSTEM_SCHED_ANNO)
        manager = SubsystemManager.getInstance()
        for method in methods:
            schedType, schedName = AnnotationHelper.getAnnotation(method, SYSTEM_SCHED_ANNO) # type: ignore
            if schedType == Sched.TYPE_RENDER:
                manager.renderSched.removeTask(schedName)
            elif schedType == Sched.TYPE_TICK:
                sched = manager.tickSched
                sched.removeTask(schedName)
            elif schedType == Sched.TYPE_FIXED:
                self.stopFixed(schedName)
            elif schedType == Sched.TYPE_EVENT:
                self._removeSchedEvents()

    def _registerRemoteFuncs(self):
        from ..remote.common import REMOTE_INNER_KEY, record
        remoteRecord = record()
        for method in AnnotationHelper.findAnnotatedMethods(self, REMOTE_INNER_KEY):
            remoteRecord[self.__class__.__name__ + '.' + method.__name__] = method.__get__(self)

    def _removeRemoteFuncs(self):
        from ..remote.common import REMOTE_INNER_KEY, record
        remoteRecord = record()
        for method in AnnotationHelper.findAnnotatedMethods(self, REMOTE_INNER_KEY):
            remoteRecord.pop(self.__class__.__name__ + '.' + method.__name__)

    def _init(self):
        SubsystemManager.getInstance()._record(self) # type: ignore
        self._fixedSchedsToAdd = {} # type: dict[str, list]
        self._schedEvents = {} # type: dict[tuple, tuple[list[function], list[function]]]
        self.fixedSchedulers = {} # type: dict[str, SimpleFixedScheduler]
        self._addListeners()
        self._addSchedMethods()
        self._registerRemoteFuncs()
        self.onInit()
        self.initialized = True

    def _destroy(self):
        self.initialized = False
        self.onDestroy()
        self._removeRemoteFuncs()
        self._removeSchedMethods()
        self._removeListeners()
        SubsystemManager.getInstance()._removeRecord(self) # type: ignore

    def _addFixedSched(self, schedulerName, schedFlag, method):
        schedList = self._fixedSchedsToAdd.get(schedulerName, [])
        schedList.append({
            'flag': schedFlag,
            'method': method
        })
        self._fixedSchedsToAdd[schedulerName] = schedList
    
    def scheduleFixed(self, schedName, period=1):
        """
        添加一个固定频率的调度器
        不要在使用注解注册的 Subsystem.onInit 调用, 此时游戏还未初始化
        """
        sched = SimpleFixedScheduler(period)
        self.fixedSchedulers[schedName] = sched
        schedTasks = self._fixedSchedsToAdd.pop(schedName, [])
        for config in schedTasks:
            task = config['method']
            schedFlag = config['flag']
            sched.scheduler.addTask(schedFlag, task)
        sched.start()
        return sched

    def stopFixed(self, schedName):
        sched = self.fixedSchedulers.pop(schedName, None)
        if sched:
            sched.cancel()
            return True
        return False


class ServerSubsystem(Subsystem):
    def __init__(self, system, engine, sysName):
        # type: (object, str, str) -> 'None'
        Subsystem.__init__(self, system, engine, sysName) # type: ignore

    def sendAllClients(self, eventName, eventData):
        self.system.BroadcastToAllClient(eventName, eventData) # type: ignore

    def sendClient(self, targetIds, eventName, eventData):
        if type(targetIds) == str or type(targetIds) == int:
            self.system.NotifyToClient(targetIds, eventName, eventData) # type: ignore
            return

        self.system.NotifyToMultiClients(targetIds, eventName, eventData) # type: ignore

    def spawnEntity(self, template, location, rot, isNpc=False, isGlobal=False):
        if type(template) == str:
            return self.system.CreateEngineEntityByTypeStr(template, location.pos, rot, dimensionId=location.dim, isNpc=isNpc, isGlobal=isGlobal) # type: ignore
        elif type(template) == dict:
            return self.system.CreateEngineEntityByNBT(template, location.pos, rot, dimensionId=location.dim, isNpc=isNpc, isGlobal=isGlobal) # type: ignore
        return None
        
    def destroyEntity(self, entityId):
        return self.system.DestroyEntity(entityId)
    
    def spawnItem(self, itemDict, location):
        return self.system.CreateEngineItemEntity(itemDict, dimensionId=location.dim, pos=location.pos) # type: ignore


class ClientSubsystem(Subsystem):

    def sendServer(self, eventName, eventData):
        self.system.NotifyToServer(eventName, eventData) # type: ignore

    def spawnEntity(self, typeStr, pos, rot):
        if type(typeStr) == str:
            return self.system.CreateClientEntityByTypeStr(typeStr, pos, rot) # type: ignore
        return None
    
    def onRender(self, dt):
        pass
    
    def destroyEntity(self, entityId):
        self.system.DestroyClientEntity(entityId) # type: ignore

    def createSfx(self, path, pos=None, rot=None, scale=None):
        return self.system.CreateEngineSfx(path, pos, rot, scale) # type: ignore
    
    def createParticle(self, path, pos):
        return self.system.CreateEngineParticle(path, pos) # type: ignore
    
    def createEffectBind(self, path, bindEntity, aniName):
        return self.system.CreateEngineEffectBind(path, bindEntity, aniName) # type: ignore
    
    def destroySfx(self, entityId):
        return self.system.DestroyEntity(entityId)


ServerSystem = serverApi.GetServerSystemCls()
ClientSystem = clientApi.GetClientSystemCls()

class _ShadowSystemServer(ServerSystem):
    pass

class _ShadowSystemClient(ClientSystem):
    pass



class subsystem:

    _firstSubsysClient = None
    _firstSubsysServer = None

    @staticmethod
    def _findFirstSubsystem():
        if isServer():
            if not subsystem._firstSubsysServer:
                subsystem._firstSubsysServer = SubsystemManager.getInstance().subsystems.values()[0] # type: ignore
            return subsystem._firstSubsysServer
        else:
            if not subsystem._firstSubsysClient:
                subsystem._firstSubsysClient = SubsystemManager.getInstance().subsystems.values()[0] # type: ignore
            return subsystem._firstSubsysClient

    @staticmethod
    def sendServer(event, data):
        client = subsystem._findFirstSubsystem() # type: ClientSubsystem
        client.sendServer(event, data)

    @staticmethod
    def sendClient(target, event, data):
        server = subsystem._findFirstSubsystem() # type: ServerSubsystem
        server.sendClient(target, event, data)

    @staticmethod
    def sendAllClients(event, data):
        server = subsystem._findFirstSubsystem() # type: ServerSubsystem
        server.sendAllClients(event, data)

    @staticmethod
    def spawnServerEntity(template, location, rot, isNpc=False, isGlobal=False):
        # type: (str, Location, tuple[float, float], bool, bool) -> str | None
        serverSubsys = subsystem._findFirstSubsystem() # type: ServerSubsystem
        return serverSubsys.spawnEntity(template, location, rot, isNpc, isGlobal)

    @staticmethod
    def spawnClientEntity(template, pos, rot):
        # type: (str|dict, tuple[float, float, float], tuple[float, float]) -> str | None
        clientSubsys = subsystem._findFirstSubsystem() # type: ClientSubsystem
        return clientSubsys.spawnEntity(template, pos, rot)

    @staticmethod
    def spawnItem(itemCls, *args, **kwargs):
        serverSubsys = subsystem._findFirstSubsystem()
        return serverSubsys.spawnItem(itemCls, *args, **kwargs)
    
    @staticmethod
    def addListener(event, fn, isCustomEvent=False):
        # type: (str, function, bool) -> str
        return subsystem._findFirstSubsystem()._addListener(event, fn, isCustomEvent)

    @staticmethod
    def removeListener(event, fn, isCustomEvent=False):
        # type: (str, function, bool) -> str
        return subsystem._findFirstSubsystem()._removeListener(event, fn, isCustomEvent)
