# -*- coding: utf-8 -*-
from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    getOneSingletonComponent, getOrCreateComponent,
    getOrCreateSingletonComponent,
    localPlayerId,
    Component, BaseCompClient,
    StateNode,
    Sched, Query, DeltaTime, EntityId,
    addTimer, vec,
)
from ..engine.architect.math.double import clamp, inf
from ..engine.architect.math.utils import forward
from ..engine.architect.plugins.input.client import InputAction, InputExComponent
from ..engine.architect.plugins.input.enum import InputState
from ..engine.architect.plugins.motion.playerMotionComp import PlayerMotionComponent
from ..lib.feature import LocalFeaturesComponent
from ..lib.stateTree import ShooterStateTreeComponent, PostureState
from ..lib.shootVfx import PlayerShooterVfxSystem


@Component()
class BayonetChargeComponent(BaseCompClient):
    cooldown = 0
    remains = 5
    enabled = False


class BayonetChargeState(StateNode):
    """蓄力状态：按住 F 进入，松开或蓄力时间结束后进入处决状态。"""

    def __init__(self, bayonetCharge, name='bayonet_charge'):
        StateNode.__init__(self, name)
        self.bayonetCharge = bayonetCharge
        self.requested = False
        self.params = None
        self.execute = None # type: BayonetExecuteState

    def canEnter(self, tree):
        return (
            tree.weapon is not None
            and self.bayonetCharge.cooldown <= 0
            and self.bayonetCharge.remains > 0
            and tree.hasFeature('bayonet')
            and self.requested
            and tree.currentStateName() in (PostureState.Idle, PostureState.Walking, PostureState.Sprinting)
        )

    def canExit(self, tree):
        return (
            not self.requested
            or not tree.hasFeature('bayonet')
            or self.bayonetCharge.remains <= 0
        )

    def enter(self, previous, tree):
        if not self.params:
            return
        tree.animEx.play(self.params['animation'], replay=True)
        PlayerShooterVfxSystem.getInstance().fovScale = 1.4
        localId = localPlayerId()
        bayonet = getOrCreateComponent(localId, BayonetChargeComponent)
        bayonet.enabled = True
        motion = getOrCreateComponent(localId, PlayerMotionComponent)
        motion.lockMovement((0, 1))

    def update(self, tree):
        # 蓄力时间耗尽后自动进入处决
        if self.bayonetCharge.remains <= 0:
            if self.execute:
                self.execute.pending = True
            tree.finishTasks()

    def exit(self, next, tree):
        # 退出蓄力时只做状态清理，不再播放处决动画；
        # 处决动画交给 BayonetExecuteState 完整播放。
        if not self.params:
            return
        PlayerShooterVfxSystem.getInstance().fovScale = 1
        bayonet = getOrCreateComponent(localPlayerId(), BayonetChargeComponent)
        bayonet.enabled = False
        bayonet.remains = 5
        bayonet.cooldown = 10
        motion = getOrCreateComponent(localPlayerId(), PlayerMotionComponent)
        motion.unlockMovement()


class BayonetExecuteState(StateNode):
    """处决状态：完整播放 executeAnimation，播完后再回 idle。"""

    def __init__(self, name='bayonet_execute'):
        StateNode.__init__(self, name)
        self.pending = False
        self.params = None
        self.chargeName = None
        self._token = 0

    def canEnter(self, tree):
        # 处决只能从 charge 状态切换过来，不能从 idle 等状态直接进入。
        return (
            tree.weapon is not None
            and tree.hasFeature('bayonet')
            and self.pending
            and self.chargeName is not None
            and tree.currentStateName() == self.chargeName
        )

    def canExit(self, tree):
        return not self.pending or not tree.hasFeature('bayonet')

    def enter(self, previous, tree):
        if not self.params:
            self.pending = False
            tree.finishTasks()
            return

        anim = self.params.get('executeAnimation')
        if not anim:
            self.pending = False
            tree.finishTasks()
            return

        self._token += 1
        token = self._token
        tree.animEx.play(anim, replay=True)

        duration = tree._getAnimDuration(tree.animEx, anim)
        if duration > 0:
            addTimer(duration, lambda token=token: self._finish(tree, token), False)
        else:
            self._finish(tree, token)

    def _finish(self, tree, token):
        if token != self._token:
            return
        self.pending = False
        tree.finishTasks()


@SubsystemClient
class BayonetFeatureSystem(ClientSubsystem):

    _chargeNode = None # type: BayonetChargeState
    _executeNode = None # type: BayonetExecuteState

    def onReady(self):
        features = getOrCreateSingletonComponent(LocalFeaturesComponent)
        features.registerFeatureHandlers(
            'bayonet',
            self._onBayonetApplied,
            self._onBayonetRemoved,
        )

    def _onBayonetApplied(self, name, params):
        stateTree = getOrCreateComponent(localPlayerId(), ShooterStateTreeComponent)
        bayonetCharge = getOrCreateComponent(localPlayerId(), BayonetChargeComponent)

        # 同一 feature 的状态放到同一个父分支下：
        # features > feature.bayonet > charge / execute
        stateTree.getOrCreateFeatureBranch('bayonet')

        charge = BayonetChargeState(bayonetCharge, 'bayonet_charge')
        charge.params = params

        execute = BayonetExecuteState('bayonet_execute')
        execute.params = params
        charge.execute = execute

        self._chargeNode = stateTree.addFeatureState('bayonet', charge, parentName='feature.bayonet')
        self._executeNode = stateTree.addFeatureState('bayonet', execute, parentName='feature.bayonet')

        if self._executeNode is not None:
            self._executeNode.chargeName = self._chargeNode.name if self._chargeNode is not None else None

        # feature 生效时启用对应输入映射，才能收到 action.bayonet
        inputEx = getOneSingletonComponent(InputExComponent)
        if inputEx:
            inputEx.enableMapping('mapping.bayonet')

    def _onBayonetRemoved(self, name):
        stateTree = getOrCreateComponent(localPlayerId(), ShooterStateTreeComponent)

        if self._chargeNode:
            stateTree.removeFeatureState(self._chargeNode.name)
            self._chargeNode = None

        if self._executeNode:
            stateTree.removeFeatureState(self._executeNode.name)
            self._executeNode = None

        stateTree.removeFeatureBranch('bayonet')

        inputEx = getOneSingletonComponent(InputExComponent)
        if inputEx:
            inputEx.disableMapping('mapping.bayonet')

    @InputAction('action.bayonet')
    def onPressBayonetCharge(self, _):
        if not self._chargeNode:
            return
        self._chargeNode.requested = True
        stateTree = getOrCreateComponent(localPlayerId(), ShooterStateTreeComponent)
        stateTree.finishTasks()

    @InputAction('action.bayonet', InputState.Completed)
    def onReleaseBayonetCharge(self, _):
        if not self._chargeNode or not self._executeNode:
            return

        stateTree = getOrCreateComponent(localPlayerId(), ShooterStateTreeComponent)

        # 只有当前确实在 charge 状态下，松开才允许进入 execute
        if stateTree.currentStateName() != self._chargeNode.name:
            self._chargeNode.requested = False
            return

        self._chargeNode.requested = False
        self._executeNode.pending = True
        stateTree.finishTasks()

    @Sched.Render()
    @Query(DeltaTime, EntityId, BayonetChargeComponent, PlayerMotionComponent)
    def handleBayonetComponent(self, dt, entityId, bayonet, motion):
        # type: (float, str, BayonetChargeComponent, PlayerMotionComponent) -> None
        if bayonet.cooldown > 0:
            bayonet.cooldown = clamp(bayonet.cooldown - dt, 0, inf)
            return
        if bayonet.enabled and bayonet.remains > 0:
            bayonet.remains = clamp(bayonet.remains - dt, 0, inf)
            motion.motion = forward(entityId) * dt * 100 + vec((0, -0.3, 0))
