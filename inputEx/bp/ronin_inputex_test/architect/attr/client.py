from ..core.export import ClientSubsystem, SubsystemClient
from ..event import EventListener
from .common import ClientAttrEvents, ReactiveBase, ReactiveDepEvents

class ReactiveAttrClient(ReactiveBase):
    def __init__(self, entityId, name, defaultValue=None, broadcast=True, serverSync=False, persistent=False):
        ReactiveBase.__init__(self, entityId, name, defaultValue)
        self.serverSync = serverSync
        self.persistent = persistent
        self.broadcast = broadcast
        self._init()

    def _init(self):
        self._loadAttr()
        self._broadcastAttr()
        self._sendServer()
        ModAttrClient.attrs[(self.entityId, self.name)] = self

    def _loadAttr(self):
        if self.persistent:
            from ..persistent.client import ClientKVDatabase
            db = ClientKVDatabase.getInstance() # type: ClientKVDatabase
            self.dbView = db.createView('attr.{}.{}'.format(self.__module__, self.entityId))
            self._value = self.dbView.get(self.name, self.defaultValue)

    def _saveAttr(self):
        if self.persistent:
            self.dbView.set(self.name, self.value)

    def onDepEvent(self, evType):
        if evType == ReactiveDepEvents.Set:
            self._saveAttr()
            self._broadcastAttr()
            self._sendServer()

    def __del__(self):
        ModAttrClient.attrs.pop((self.entityId, self.name))

    def _sendServer(self):
        if self.serverSync:
            sys = ModAttrClient.getInstance() # type: ModAttrClient
            sys.sendServer(ClientAttrEvents.ServerSync, {
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
            ModAttrClient.getInstance().broadcast(ClientAttrEvents.AttrChange, {
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
        return attr.create(entity, name, defaultValue, False, False, False)
    @staticmethod
    def store(name, entity, defaultValue=None):
        """
        创建一个可存储属性，它不会同步，不会广播事件
        """
        return attr.create(entity, name, defaultValue, False, False, True)
    @staticmethod
    def remote(name, entity, defaultValue=None, persistent=False):
        """
        创建一个远程属性，它不会广播，但是会同步到服务器
        """
        return attr.create(entity, name, defaultValue, False, True, persistent)
    @staticmethod
    def shared(name, entity, defaultValue=None, persistent=False):
        """
        创建一个共享属性，它既会广播又会同步到服务器
        """
        return attr.create(name, entity, defaultValue, True, True, persistent)
    @staticmethod
    def create(name, entity, defaultValue=None, broadcast=True, serverSync=False, persistent=False):
        existed = ModAttrClient.attrs.get((entity, name))
        if existed:
            return existed
        return ReactiveAttrClient(entity, name, defaultValue, broadcast, serverSync, persistent)


@SubsystemClient
class ModAttrClient(ClientSubsystem):
    attrs = {}

    @EventListener(ClientAttrEvents.ServerSync, isCustomEvent=True)
    def onServerSync(self, ev):
        ref = ModAttrClient.attrs.get((ev['id'], ev['name'])) # type: ReactiveAttrClient
        if not ref:
            return
        ref._sync(ev['value'])