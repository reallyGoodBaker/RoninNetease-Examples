from ....compact import Component, BaseCompClient
from ..utils.mappingContext import InputMapping
from ..utils.inputValue import InputValue


@Component(singleton=True)
class InputExComponent(BaseCompClient):
    def onCreate(self, entityId):
        self.inputMappings = [] # type: list[InputMapping]
        self._rawInputs = {} # type: dict[tuple[str, str], InputValue]
        self.actionValues = {} # type: dict[str, float|tuple[float, float, float]|tuple[float, float]]
        self._triggerStates = {} # type: dict[str, int]
        self.preventUse = False
        self.preventAttack = False
        self.preventTap = False
        self.preventHold = False


    def updateInputValue(self, inputType, key, value):
        mappingKey = (inputType, key)
        if mappingKey not in self._rawInputs:
            self._rawInputs[mappingKey] = InputValue(value)
        else:
            self._rawInputs[mappingKey].rawValue = value

    def getInputValue(self, inputType, key):
        mappingKey = (inputType, key)
        if mappingKey not in self._rawInputs:
            return InputValue()
        return self._rawInputs[mappingKey]
    
    def enableMapping(self, name):
        mapping = InputMapping.get(name)
        if not mapping:
            return False
        self.inputMappings.append(mapping)
        if len(self.inputMappings):
            self.inputMappings.sort(key=lambda x: x.priority, reverse=True)
        return True
    

    def disableMapping(self, name):
        mapping = InputMapping.get(name)
        if not mapping or mapping not in self.inputMappings:
            return False
        self.inputMappings.remove(mapping)
        if len(self.inputMappings):
            self.inputMappings.sort(key=lambda x: x.priority, reverse=True)
        return True
    
    def isMappingEnabled(self, name):
        mapping = InputMapping.get(name)
        if not mapping:
            return False
        return mapping in self.inputMappings
    
    def enableMappings(self, *names):
        for name in names:
            self.enableMapping(name)

    def disableMappings(self, *names):
        for name in names:
            self.disableMapping(name)