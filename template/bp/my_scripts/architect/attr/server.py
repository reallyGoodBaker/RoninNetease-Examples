from ..core.export import ServerSubsystem, SubsystemServer
from ..event import EventListener
from .common import ServerAttrEvents, ReactiveBase, ReactiveDepEvents

class ClientSyncMode:
    Disabled = 0
    Target = 1
    All = 2

class ReactiveAttrServer(ReactiveBase):
    def __init__(self, entityId, name, defaultValue=None, broadcast=True, clientSync=ClientSyncMode.Target, persistent=False):
        ReactiveBase.__init__(self, entityId, name, defaultValue)
        self.clientSync = clientSync
        self.persistent = persistent
        self.broadcast = broadcast
        self._init()

    def _init(self):
        self._loadAttr()
        self._broadcastAttr()
        self._sendClients()
        ModAttrServer.attrs[(self.entityId, self.name)] = self

    def _loadAttr(self):
        if self.persistent:
            from ..persistent.server import ServerKVDatabase
            db = ServerKVDatabase.getInstance() # type: ServerKVDatabase
            self.dbView = db.createView('attr.{}.{}'.format(self.__module__, self.entityId))
            self._value = self.dbView.get(self.name, self.defaultValue)

    def _saveAttr(self):
        if self.persistent:
            self.dbView.set(self.name, self.value)

    def onDepEvent(self, evType):
        if evType == ReactiveDepEvents.Set:
            self._saveAttr()
            self._broadcastAttr()
            self._sendClients()

    def __del__(self):
        ModAttrServer.attrs.pop((self.entityId, self.name))

    def _sendClients(self):
        if not self.clientSync:
            return

        sys = ModAttrServer.getInstance() # type: ModAttrServer
        if self.clientSync == ClientSyncMode.Target:
            sys.sendClient(self.entityId, ServerAttrEvents.ClientSync, {
                'id': self.entityId,
                'name': self.name,
                'value': self._value
            })
        elif self.clientSync == ClientSyncMode.All:
            sys.sendAllClients(ServerAttrEvents.ClientSync, {
                'id': self.entityId,
                'name': self.name,
                'value': self._value
            })

    def _sync(self, value):
        self._value = value
        self._saveAttr()
        self._broadcastAttr()

    def _broadcastAttr(self):
        if self.broadcast:
            ModAttrServer.getInstance().broadcast(ServerAttrEvents.AttrChange, {
                'id': self.entityId,
                'name': self.name,
                'value': self._value,
                'old': self.oldValue,
            })


class attr:
    @staticmethod
    def mut(name, entity, defaultValue=None):
        """
        创建一个可变属性，它不会同步，不会保存，但是会广播到事件系统
        """
        return attr.create(entity, name, defaultValue, True, False, False)
    @staticmethod
    def store(name, entity, defaultValue=None):
        """
        创建一个可存储属性，它不会同步，不会广播事件
        """
        return attr.create(entity, name, defaultValue, False, False, True)
    @staticmethod
    def remote(name, entity, defaultValue=None, persistent=False):
        """
        创建一个远程属性，它不会广播，但是会同步到指定客户端
        """
        return attr.create(entity, name, defaultValue, False, True, persistent)
    @staticmethod
    def shared(name, entity, defaultValue=None, persistent=False):
        """
        创建一个共享属性，它既会广播又会同步到所有客户端
        """
        return attr.create(entity, name, defaultValue, True, True, persistent)
    @staticmethod
    def create(name, entity, defaultValue=None, broadcast=True, serverSync=False, persistent=False):
        existed = ModAttrServer.attrs.get((entity, name))
        if existed:
            return existed
        return ReactiveAttrServer(entity, name, defaultValue, broadcast, serverSync, persistent)



@SubsystemServer
class ModAttrServer(ServerSubsystem):
    attrs = {}

    @EventListener(ServerAttrEvents.ClientSync, isCustomEvent=True)
    def onClientSync(self, ev):
        ref = ModAttrServer.attrs.get((ev['id'], ev['name'])) # type: ReactiveAttrServer
        if not ref:
            return
        ref._sync(ev['value'])