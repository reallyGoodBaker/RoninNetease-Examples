from ...core.basic import isServer, compClient, compServer
from ...core.unreliable import Unreliable
from .types import MolangReadable, MolangMutable, EntityMolangMutable, EntityMolangReadable


class NamedVariable(Unreliable, MolangMutable):
    def __init__(self, name):
        Unreliable.__init__(self)
        self.name = name
        self._cachedVariable = None

    def getMolangName(self):
        return 'v.' + self.name

    def _molangComp(self, actorId):
        if isServer():
            return compServer.CreateQueryVariable(actorId)
        else:
            return compClient.CreateQueryVariable(actorId)

    def getValue(self, actorId, defaultValue=0): # type: ignore
        molang = self._molangComp(actorId)
        result = molang.EvalMolangExpression('v.' + self.name)
        if result.get('error'):
            self._handleError(result['error'])
            return defaultValue
        return result['value']
    
    def setValue(self, actorId, value):
        molang = self._molangComp(actorId)
        molang.EvalMolangExpression('variable.{} = {};'.format(self.name, value))



class NamedEntityVariable(EntityMolangMutable):
    _serverVarRecord = {}
    _clientVarRecord = {}

    @classmethod
    def _molangComp(cls, entity):
        if isServer():
            if entity not in cls._serverVarRecord:
                cls._serverVarRecord[entity] = compServer.CreateQueryVariable(entity)
            return cls._serverVarRecord[entity]
        else:
            if entity not in cls._clientVarRecord:
                cls._clientVarRecord[entity] = compClient.CreateQueryVariable(entity)
            return cls._clientVarRecord[entity]

    def __init__(self, entity, name, defaultValue=0):
        self.comp = NamedEntityVariable._molangComp(entity)
        self.name = name
        self.setValue(defaultValue)

    def getValue(self): # type: ignore
        return self.comp.EvalMolangExpression('v.' + self.name)['value']

    def setValue(self, value):
        self.comp.EvalMolangExpression('variable.{} = {};'.format(self.name, float(value)))

    def getName(self):
        return 'v.' + self.name