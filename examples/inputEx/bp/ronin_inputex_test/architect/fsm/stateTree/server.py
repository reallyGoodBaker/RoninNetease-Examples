from ...component import BaseCompServer
from .common import StateTree, StateNode
from ...core.export import SubsystemServer, ServerSubsystem
from ...core.basic import compServer, isServer
from ...level.server import LevelServer
from mod.common.minecraftEnum import EntityType, AttrType

class StateTreeCompServer(BaseCompServer, StateTree):
    def onCreate(self, entityId):
        StateTree.__init__(self, entityId)
        StateTreeServerSubsystem._comps.add(self)
        self.enabled = False

class StateNodeServer(StateNode):
    def __init__(self, name='unknown', subsystem=None):
        # type: (str, ServerSubsystem|None) -> None
        StateNode.__init__(self, name)
        self.subsys = subsystem

    @staticmethod
    def markVariant(entityId, value=None):
        defs = compServer.CreateEntityDefinitions(entityId)
        if value is None:
            return defs.GetMarkVariant()
        else:
            defs.SetMarkVariant(value)

    @staticmethod
    def playSound(entityId, soundName):
            x, y, z = compServer.CreatePos(entityId).GetPos()
            LevelServer.command.SetCommand('playsound {} @a {} {} {}'.format(soundName, x, y, z))

    @staticmethod
    def movement(entityId, enabled=True):
        if not isServer():
            return
        compServer.CreateCommand(entityId).SetCommand(
            'inputpermission set @s movement {}'.format('enabled' if enabled else 'disabled'),
            entityId
        )
        compServer.CreateEntityEvent(entityId).TriggerCustomEvent(entityId, 'add_movable' if enabled else 'remove_movable')
        if compServer.CreateEngineType(entityId).GetEngineType() != EntityType.Player:
            if enabled:
                compServer.CreateAttr(entityId).ResetToDefaultValue(AttrType.SPEED)
            else:
                compServer.CreateAttr(entityId).SetAttrValue(AttrType.SPEED, 0.01)

    @staticmethod
    def camera(entityId, enabled=True):
        if not isServer():
            return
        compServer.CreateCommand(entityId).SetCommand(
            'inputpermission set @s camera {}'.format('enabled' if enabled else 'disabled'),
            entityId
        )

    def createChild(self, name, cls):
        # type: (str, type[StateNodeServer]) -> StateNodeServer
        ctor = cls or StateNodeServer
        child = ctor(name, self.subsys)
        self.addChildren(child)
        return child

@SubsystemServer
class StateTreeServerSubsystem(ServerSubsystem):
    _comps = set() # type: set[StateTreeCompServer]

    def onInit(self):
        self.canTick = True

    def onUpdate(self, dt):
        for comp in StateTreeServerSubsystem._comps:
            if comp.enabled:
                comp.execute()