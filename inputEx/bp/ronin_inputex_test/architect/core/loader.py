from .subsystem import SubsystemManager, Subsystem, _ShadowSystemClient, _ShadowSystemServer, subsystem
from .basic import isServer, clientApi, serverApi
from .contextRecorder import ContextRecorder, Context
from .configurator import modConf, __modname__, __framework__, __dirname__, VendorPlugins, UserPlugins

from ..utils.enhance.fn import compVer



class PluginBase(object):

    def onCreate(self):
        # type: () -> None
        pass

    def onAttach(self, manager):
        # type: (SubsystemManager) -> None
        pass

    def onReady(self, manager):
        # type: (SubsystemManager) -> None
        pass

    def onRegisterComponent(self, compCls):
        # type: (list[type]) -> None
        pass

    def onAddSubsystem(self, subsystem):
        # type: (Subsystem) -> None
        pass

    def onRemoveSubsystem(self, subsystem):
        # type: (Subsystem) -> None
        pass

    def onDestroy(self):
        # type: () -> None
        pass


_REGISTERED_SER_PLUGINS = {} # type: dict[str, _PluginHost]
_REGISTERED_CLI_PLUGINS = {} # type: dict[str, _PluginHost]
_LOADED_SERVER_PLUGINS = {} # type: dict[str, PluginBase]
_LOADED_CLIENT_PLUGINS = {} # type: dict[str, PluginBase]


def _plugins():
    return _LOADED_SERVER_PLUGINS if isServer() else _LOADED_CLIENT_PLUGINS

def getPlugin(name):
    # type: (str) -> PluginBase
    return _LOADED_SERVER_PLUGINS[name] if isServer() else _LOADED_CLIENT_PLUGINS[name]

def hasPlugin(name):
    # type: (str) -> bool
    return name in _plugins()


depComps = ContextRecorder.get('depComps')
depSubsystems = ContextRecorder.get('depSubsystems')

class _PluginHost(object):
    def __init__(self, name, ver, author, desc, compCls):
        # type: (str, list[int], str, str, type[PluginBase]) -> None
        self.name = name
        self.ver = ver
        self.author = author
        self.desc = desc
        self.compCls = compCls
        self._inst = None
        self._capturedComps = []
        self._capturedSubsystems = []

    def create(self):
        loadedPlugins = _plugins()
        if self.name in loadedPlugins:
            print('[INFO] Plugin {} already loaded')
            return
        compModule = self.compCls.__module__
        depComps.start(compModule)
        depSubsystems.start(compModule)
        try:
            _inst = self.compCls()
            _inst.onCreate()
        finally:
            depComps.stop()
            depSubsystems.stop()
        # 按模块前缀扫描所有 context 记录，确保被其他插件预导入的组件/子系统也能被捕获
        prefix = compModule.rsplit('.', 1)[0]
        seen = set()
        for ctx in Context._contexts.values():
            for (cat, cls), _ in ctx.iter():
                if not hasattr(cls, '__module__'):
                    continue
                if cls in seen:
                    continue
                if not cls.__module__.startswith(prefix):
                    continue
                seen.add(cls)
                if cat == 'depSubsystems':
                    self._capturedSubsystems.append(cls)
                elif cat == 'depComps':
                    self._capturedComps.append(cls)
        self._inst = _inst
        return _inst
    
    def destroy(self):
        if self._inst is None:
            return
        self._inst.onDestroy()
        if self._capturedComps:
            for _comp in self._capturedComps:
                pass
        if self._capturedSubsystems:
            for _sys in self._capturedSubsystems:
                LoaderUtils.getManager().removeSubsystem(_sys)

    def load(self, manager):
        # type: (SubsystemManager) -> None
        registerList = _REGISTERED_SER_PLUGINS if isServer() else _REGISTERED_CLI_PLUGINS
        if self.name not in registerList:
            raise Exception('Plugin {} not registered'.format(self.name))
        _LOADED_PLUGINS = _plugins()
        if self.name in _LOADED_PLUGINS:
            print('[INFO] Plugin {} already loaded')
            return
        _inst = self._inst
        _inst.onAttach(manager)
        _LOADED_PLUGINS[self.name] = _inst
        self._inst = _inst


def _upgradePlugin(pluginHost, newCls, name, ver, author, desc):
    # type: (_PluginHost, type[PluginBase], str, list[int], str, str) -> None
    pluginHost.compCls = newCls
    pluginHost.ver = ver
    pluginHost.author = author
    pluginHost.desc = desc
    pluginHost.name = name

    loadedPlugins = _plugins()
    if name in loadedPlugins:
        pluginHost._inst.onDestroy()
        _inst = pluginHost.create()
        loadedPlugins[name] = _inst
        from .subsystem import SubsystemManager
        _inst.onAttach(SubsystemManager.getInstance())


def Plugin(name, ver=[0, 0, 1], author='Unknown', desc='Unknown'):
    def _decorator(cls):
        # type: (type) -> type
        registerList = _REGISTERED_SER_PLUGINS if isServer() else _REGISTERED_CLI_PLUGINS
        if cls not in registerList:
            registerList[name] = _PluginHost(name, ver, author, desc, cls)
            registerList[name].create()
        else:
            registered = registerList[name]
            if compVer(ver, registered.ver) > 0:
                _upgradePlugin(registered, cls, name, ver, author, desc)
        return cls
    return _decorator


def pluginPath(name):
    # type: (str) -> str
    return name.replace(
        '$vendor',
        VendorPlugins
    ).replace(
        '$user',
        UserPlugins
    ) + ('.server' if isServer() else '.client')


def _scanPlugins(isHost):
    # type: (bool) -> None
    getConf = modConf()
    _plugins = getConf('PLUGINS')
    if _plugins is None:
        return
    for _name in _plugins:
        _absPath = pluginPath(_name)
        depComps.start(_absPath)
        depSubsystems.start(_absPath)
        try:
            if isHost:
                serverApi.ImportModule(_absPath)
            else:
                clientApi.ImportModule(_absPath)
        finally:
            depComps.stop()
            depSubsystems.stop()


def _loadPlugins(manager, isHost):
    # type: (SubsystemManager, bool) -> None
    _scanPlugins(isHost)
    registerList = _REGISTERED_SER_PLUGINS if isHost else _REGISTERED_CLI_PLUGINS
    for _name, _host in registerList.items():
        try:
            _host.load(manager)
            print('[INFO] Loaded plugin: ' + _host.name + ' by ' + _host.author + '\n' + _host.desc)
        except Exception as e:
            print('[ERROR] Failed to load plugin ' + _name)

def _readyPlugins(manager):
    for _host in _plugins().values():
        try:
            _host.onReady(manager)
        except Exception as e:
            print('[ERROR] Failed to ready plugin ' + _host.__class__.__name__)



ServerSystem = serverApi.GetServerSystemCls()
ClientSystem = clientApi.GetClientSystemCls()

RONIN_ENGINE = 'RoninFramework'
RONIN_SYSTEM_CLI = 'LoaderClient'
RONIN_SYSTEM_SER = 'LoaderServer'

conf = modConf()

CURRENT_ENGINE = conf('MOD_ENGINE_NAME')
CURRENT_SYSTEM = conf('MOD_SYSTEM_NAME')



class FrameworkLoaderServer(ServerSystem):
    _recordedSystems = {} # type: dict[tuple[str, str], SubsystemManager]

    @classmethod
    def getLoader(cls):
        # type: () -> FrameworkLoaderServer
        loaderServer = serverApi.GetSystem(RONIN_ENGINE, RONIN_SYSTEM_SER)
        if not loaderServer:
            loaderServer = serverApi.RegisterSystem(
                RONIN_ENGINE,
                RONIN_SYSTEM_SER,
                cls.__module__ + '.' + cls.__name__
            )
        return loaderServer

    def recordSystem(self, engine, system, manager):
        self._recordedSystems[(engine, system)] = manager

    def getManager(self, engine=CURRENT_ENGINE, system=CURRENT_SYSTEM):
        # type: (str, str) -> SubsystemManager | None
        visitor = (engine, system)
        return self._recordedSystems.get(visitor, None)


class FrameworkLoaderClient(ClientSystem):
    _recordedSystems = {} # type: dict[tuple[str, str], SubsystemManager]

    @classmethod
    def getLoader(cls):
        # type: () -> FrameworkLoaderClient
        loaderClient = clientApi.GetSystem(RONIN_ENGINE, RONIN_SYSTEM_CLI)
        if not loaderClient:
            loaderClient = clientApi.RegisterSystem(
                RONIN_ENGINE,
                RONIN_SYSTEM_CLI,
                cls.__module__ + '.' + cls.__name__
            )
        return loaderClient

    def recordSystem(self, engine, system, manager):
        self._recordedSystems[(engine, system)] = manager

    def getManager(self, engine=CURRENT_ENGINE, system=CURRENT_SYSTEM):
        # type: (str, str) -> SubsystemManager | None
        visitor = (engine, system)
        return self._recordedSystems.get(visitor, None)


class LoaderUtils(object):

    @staticmethod
    def getLoader():
        if isServer():
            return FrameworkLoaderServer.getLoader()
        else:
            return FrameworkLoaderClient.getLoader()

    @staticmethod
    def getManager(engine=CURRENT_ENGINE, system=CURRENT_SYSTEM):
        # type: (str, str) -> SubsystemManager | None
        return LoaderUtils.getLoader().getManager(engine, system)

    @staticmethod
    def createManager():
        # type: () -> SubsystemManager
        loader = LoaderUtils.getLoader()
        isHost = isServer()
        api = serverApi if isHost else clientApi
        shadowSystemCls = _ShadowSystemServer if isHost else _ShadowSystemClient
        system = api.GetSystem(CURRENT_ENGINE, CURRENT_SYSTEM) or api.RegisterSystem(CURRENT_ENGINE, CURRENT_SYSTEM, shadowSystemCls.__module__ + '.' + shadowSystemCls.__name__)
        manager = SubsystemManager(system, CURRENT_ENGINE, CURRENT_SYSTEM)
        loader.recordSystem(CURRENT_ENGINE, CURRENT_SYSTEM, manager)
        if isHost:
            SubsystemManager.instServer = manager
        else:
            SubsystemManager.instClient = manager
        return manager


def SubsystemClient(subsystemCls):
    """
    Decorator to auto register subsystem class
    """
    manager = LoaderUtils.getManager()
    if not manager:
        raise RuntimeError('错误的加载顺序: SubsystemClient 装饰器被调用时，SubsystemManager 尚未创建，请确保在引擎加载完成后再使用 SubsystemClient 装饰器')
    if not isServer():
        depSubsystems.record(subsystemCls)
        manager.registerSubsystem(subsystemCls)
    return subsystemCls


def SubsystemServer(subsystemCls):
    """
    Decorator to auto register subsystem class
    """
    manager = LoaderUtils.getManager()
    if not manager:
        raise RuntimeError('错误的加载顺序: SubsystemServer 装饰器被调用时，SubsystemManager 尚未创建，请确保在引擎加载完成后再使用 SubsystemServer 装饰器')
    if isServer():
        depSubsystems.record(subsystemCls)
        manager.registerSubsystem(subsystemCls)
    return subsystemCls


def createServer():
    manager = LoaderUtils.createManager()
    manager.INITIALIZED.on(lambda: _loadPlugins(manager, True))
    manager.PRELOADED.on(lambda: _readyPlugins(manager))
    manager.createServer()


def createClient():
    manager = LoaderUtils.createManager()
    manager.INITIALIZED.on(lambda: _loadPlugins(manager, False))
    manager.PRELOADED.on(lambda: _readyPlugins(manager))
    manager.createClient()