from .common import MolangMutable
from ...core.basic import compServer
from ...core.unreliable import Unreliable
from ...core.export import ServerSubsystem, SubsystemServer
from ...event import EventListener

class NamedProperty(MolangMutable, Unreliable):
    def __init__(self, name):
        self.name = name
        Unreliable.__init__(self)

    def _molang(self, actorId):
        return compServer.CreateQueryVariable(actorId)

    def getValue(self, actorId): # type: ignore
        result = self._molang(actorId).EvalMolangExpression("v.property('{}')".format(self.name))
        if result['error']:
            self._handleError(result['error'])
            return None
        return result['value']

    def setValue(self, actorId, value):
        self._molang(actorId).SetPropertyValue(self.name, value)


@SubsystemServer
class MolangServer(ServerSubsystem):

    @EventListener('ronin_molang_query', isCustomEvent=True)
    def _handleQuery(self, event):
        self.sendAllClients('ronin_molang_query', event.dict())

    def sendQuery(self, id, name, value):
        self.sendAllClients('ronin_molang_query', {
            'actorId': id,
            'name': name,
            'value': value
        })