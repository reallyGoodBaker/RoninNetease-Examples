class ClientAttrEvents:
    AttrChange = '_attr_change_'
    ServerSync = '_attr_sync_'

class ServerAttrEvents:
    AttrChange = '_attr_change_'
    ClientSync = '_attr_sync_'

class ReactiveDepEvents:
    Get = 0
    Set = 1

class ReactiveBase:
    def __init__(self, entityId, name, defaultValue=None):
        self.entityId = entityId
        self.name = name
        self.defaultValue = defaultValue
        self._value = defaultValue
        self.oldValue = defaultValue

    def onDepEvent(self, evType):
        pass

    @property
    def value(self):
        self.onDepEvent(ReactiveDepEvents.Get)
        return self._value
    
    @value.setter
    def value(self, value):
        self.oldValue = self._value
        self._value = value
        self.onDepEvent(ReactiveDepEvents.Set)

