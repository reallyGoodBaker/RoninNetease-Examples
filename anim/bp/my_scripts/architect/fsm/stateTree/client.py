from ...component import BaseCompClient
from .common import StateTree
from ...core.export import SubsystemClient, ClientSubsystem

class StateTreeCompClient(BaseCompClient, StateTree):
    def onCreate(self, entityId):
        StateTree.__init__(self, entityId)
        StateTreeClientSubsystem._comps.add(self)
        self.enabled = False

@SubsystemClient
class StateTreeClientSubsystem(ClientSubsystem):
    _comps = set() # type: set[StateTreeCompClient]

    def onInit(self):
        self.canTick = True

    def onUpdate(self, dt):
        for comp in StateTreeClientSubsystem._comps:
            if comp.enabled:
                comp.execute()