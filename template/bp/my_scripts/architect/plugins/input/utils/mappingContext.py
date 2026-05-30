from .modifier import InputModifier
from .trigger import InputTrigger
from ..enum import InputType


class InputBinding(object):
    def __init__(self, inputType, key, action, modifiers=[], triggers=[]):
        # type: (InputType, str, str, list[InputModifier], list[InputTrigger]) -> None
        self.inputType = inputType
        self.key = key
        self.action = action
        self.modifiers = modifiers
        self.triggers = triggers


class InputMapping(object):
    _registry = {}

    def __init__(self, name, bindings=[], priority=0):
        # type: (str, list[InputBinding], int) -> None
        self.priority = priority
        self.name = name
        self.bindings = bindings
        InputMapping._registry[name] = self

    @classmethod
    def get(cls, name):
        # type: (str) -> InputMapping
        return cls._registry.get(name)