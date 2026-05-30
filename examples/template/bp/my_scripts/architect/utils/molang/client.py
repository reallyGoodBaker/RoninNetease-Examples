from ...core.unreliable import Unreliable
from ...core.basic import compClient, clientApi
from .common import MolangMutable
from ...core.export import ClientSubsystem, SubsystemClient
from ...event.core import EventSignal
from ...event import EventListener

_queryVariableUsed = {}

def _recordQueryVariableUsage(name, actorId):
    users = _queryVariableUsed.get(name, set()) # type: set
    users.add(actorId)

class QueryVariable(MolangMutable, Unreliable):
    def __init__(self, name, defaultValue=0):
        Unreliable.__init__(self)
        self.name = 'query.mod.' + name
        self.rawName = name
        self.defaultValue = defaultValue
        self.OnValueChanged = EventSignal()
        compClient.CreateQueryVariable(clientApi.GetLevelId()).Register(self.name, self.defaultValue)

    def _molangComp(self, actorId):
        return compClient.CreateQueryVariable(actorId)

    def getValue(self, actorId): # type: ignore
        molang = self._molangComp(actorId)
        return molang.Get(self.name)

    def setValue(self, actorId, value): # type: ignore
        molang = self._molangComp(actorId)
        result = molang.Set(self.name, value)
        self.OnValueChanged.emit(actorId, value)
        _recordQueryVariableUsage(self.name, actorId)
        return result


class ReactiveQueryVariable(QueryVariable):
    def __init__(self, name, calc=None):
        QueryVariable.__init__(self, name, 0)
        self.calc = calc

    def update(self, actorId):
        self.setValue(actorId, self.calc(actorId)) # type: ignore


reactiveQueryVariables = {} # type: dict[str, ReactiveQueryVariable]

def _addReactiveQueryVariable(name, calc=None, onUpdate=None):
    if not callable(calc):
        return
    qv = reactiveQueryVariables.get(name, ReactiveQueryVariable(name, calc)) # type: ReactiveQueryVariable
    reactiveQueryVariables[name] = qv
    if callable(onUpdate):
        qv.OnValueChanged.on(onUpdate)

def _updateReactiveQuery(actorId, name, value):
    if actorId == clientApi.GetLocalPlayerId():
        return
    qv = reactiveQueryVariables.get(name)
    if not qv:
        return
    qv.setValue(actorId, value)


@SubsystemClient
class MolangClient(ClientSubsystem):

    @EventListener('ronin_molang_query', isCustomEvent=True)
    def onQuery(self, event):
        _updateReactiveQuery(event.actorId, event.name, event.value)

    def onInit(self):
        self.canTick = True

    def broadcastQuery(self, actorId, name, value):
        self.sendServer('ronin_molang_query', {
            'actorId': actorId,
            'name': name,
            'value': value
        })

    def onRender(self, dt):
        for name, users in _queryVariableUsed.items():
            qv = reactiveQueryVariables.get(name)
            if not qv:
                continue
            for actorId in users:
                qv.update(actorId)


def MolangQuery(shared=False):
    def decorator(func):
        name = func.__name__
        if shared:
            def onChange(actorId, value):
                clientSys = MolangClient.getInstance() # type: ignore
                clientSys.broadcastQuery(actorId, name, value) # type: ignore
            _addReactiveQueryVariable(name, func, onChange)
        else:
            _addReactiveQueryVariable(name, func)
        return func
    return decorator