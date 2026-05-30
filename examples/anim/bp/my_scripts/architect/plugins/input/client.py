from ...core.loader import Plugin, PluginBase
from ...component import createSingletonComponent
from ...event import CustomEvent

from .components.inputEx import InputExComponent
from .enum import IA_EVENT_PREFIX, InputState


@Plugin(
    'InputExPlugin',
    [1, 0, 1],
    'RGB39',
    'Extended input plugin'
)
class InputExPlugin(PluginBase):
    def onCreate(self):
        from .components.inputEx import InputExComponent
        from .systems import inputExClient

    def onReady(self, manager):
        self._bindInputEx()

    def _bindInputEx(self):
        createSingletonComponent(InputExComponent)


def InputAction(actionName, inputState=InputState.Triggered):
    return CustomEvent(IA_EVENT_PREFIX + actionName + str(inputState))