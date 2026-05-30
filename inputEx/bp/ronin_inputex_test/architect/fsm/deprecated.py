# -*- coding: utf-8 -*-

"""
TODO: 临时设计的经典 FSM 框架，不推荐在ECS中嵌入
"""

from ..core.unreliable import Unreliable
from ..core.basic import compClient, compServer, isServer
from mod.common.minecraftEnum import AttrType, EntityType
from ..level.server import LevelServer

class State:
    def __init__(self, fsm):
        self.entityId = fsm.entityId
        self.fsm = fsm # type: Fsm
        self.stateTime = 0

    def onEvent(self, type, data):
        pass

    def onEnter(self):
        pass

    def onExit(self):
        pass

    def onUpdate(self):
        pass

    def getFsm(self):
        return self.fsm

    def markVariant(self, value=None):
        compFact = compServer if isServer() else compClient
        defs = compFact.CreateEntityDefinitions(self.entityId) # type: ignore
        if value is None:
            return defs.GetMarkVariant()
        else:
            defs.SetMarkVariant(value)

    def playSound(self, soundName):
            x, y, z = compServer.CreatePos(self.entityId).GetPos()
            LevelServer.command.SetCommand('playsound {} @a {} {} {}'.format(soundName, x, y, z))

    def movement(self, enabled=True):
        if not isServer():
            return
        compServer.CreateCommand(self.entityId).SetCommand(
            'inputpermission set @s movement {}'.format('enabled' if enabled else 'disabled'),
            self.entityId
        )
        compServer.CreateEntityEvent(self.entityId).TriggerCustomEvent(self.entityId, 'add_movable' if enabled else 'remove_movable')
        if compServer.CreateEngineType(self.entityId).GetEngineType() != EntityType.Player:
            if enabled:
                compServer.CreateAttr(self.entityId).ResetToDefaultValue(AttrType.SPEED)
            else:
                compServer.CreateAttr(self.entityId).SetAttrValue(AttrType.SPEED, 0.01)

    def camera(self, enabled=True):
        if not isServer():
            return
        compServer.CreateCommand(self.entityId).SetCommand(
            'inputpermission set @s camera {}'.format('enabled' if enabled else 'disabled'),
            self.entityId
        )


class Fsm(Unreliable):
    def __init__(self, entityId,  defaultStateCls, name='default'):
        Unreliable.__init__(self)
        self.entityId = entityId
        defaultState = defaultStateCls(self)
        self.states = {
            name: defaultState
        }
        self.defaultState = defaultState # type: State
        self.currentState = defaultState # type: State
        self.currentStateName = name # type: str
        self.defaultStateName = name # type: str
        self.context = {}

    def onCreated(self):
        pass

    def addState(self, name, stateCls):
        self.states[name] = stateCls(self)

    def addStateMapping(self, states):
        for stateName, stateCls in states.items():
            self.addState(stateName, stateCls)

    def getState(self, name):
        return self.states[name]

    def transitionTo(self, name):
        state = self.states[name]
        hasCanEnter = hasattr(state, 'canEnter')
        if not hasCanEnter and name == self.currentStateName:
            return False
        if not hasCanEnter or state.canEnter():
            if self._callExit(self.currentState):
                self.currentState = state
                self.currentStateName = name
                return self._callEnter(self.currentState)
        return False

    def _callExit(self, state):
        try:
            state.onExit()
            return True
        except Exception:
            self.currentState = self.defaultState
            return False

    def _callEnter(self, state):
        try:
            state.onEnter()
            state.stateTime = 0
            return True
        except Exception:
            self.currentState = self.defaultState
            return False

    def callUpdate(self):
        self.currentState.stateTime += 1
        self.tryCall(self.currentState.onUpdate)