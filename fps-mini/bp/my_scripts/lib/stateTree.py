# -*- coding: utf-8 -*-
from ..engine.architect.compact import (
    Component, BaseCompClient, StateTree, StateNode, addTimer,
)
from .gunBasic import GunBasic, GunState
from .stats import stats
from .render import registerWeaponAnimations
from .gunSmith import GunSmithUi


@Component()
class ShooterStateTreeComponent(BaseCompClient, StateTree):
    """
    轻量状态树组件。

    不使用 engine 内置 StateTreeCompClient 的全局子系统轮询，
    由 ShooterSystem 自己负责：
      1. getOrCreateComponent 创建/获取组件
      2. bindOwner() 把 ShooterSystem 绑定为 owner
      3. 每帧调用 stateTree.execute()
    """

    def onCreate(self, entityId):
        StateTree.__init__(self, entityId)
        self.owner = None

    def bindOwner(self, owner):
        # type: (object) -> ShooterStateTreeComponent
        self.owner = owner
        return self

    def buildDefaultTree(self):
        """构建 ShooterSystem 使用的默认状态树。"""
        self.createNode(NativeMinecraftState, 'native')
        armedNode = self.createNode(EquipAnyWeapon, 'armed')
        self.createNode(SprintingState, PostureState.Sprinting, armedNode)
        self.createNode(ReloadingState, PostureState.Reloading, armedNode)
        self.createNode(FiringState, PostureState.Firing, armedNode)
        self.createNode(WalkingState, PostureState.Walking, armedNode)
        self.createNode(GunSmithState, PostureState.GunSmith, armedNode)

        # feature 分支：只属于枪械，挂在 armed 下。
        # 放在 gunsmith 之后、idle 之前，不会打断换弹/射击/奔跑/改枪等更高优先级状态。
        self.createNode(FeaturesBranch, 'features', armedNode)

        self.createNode(IdleState, PostureState.Idle, armedNode)

    def addFeatureState(self, featureName, node, parentName='features'):
        """
        向 armed > features 分支动态添加一个 feature 状态节点。

        :param featureName: 功能名，如 'bayonet'
        :param node: StateNode 实例
        :param parentName: 父节点名，默认 features
        :return: 实际挂载的 StateNode
        """
        if not node.name:
            node.name = node.__class__.__name__
        node.name = 'feature.{}.{}'.format(featureName, node.name)

        existed = self.findNamedNode(node.name)
        if existed:
            return existed

        parent = self.findNamedNode(parentName)
        if parent is None:
            return None

        parent.addChildren(node)
        return node

    def removeFeatureState(self, nodeName):
        """
        从状态树中移除一个动态添加的 feature 状态节点。
        如果当前正处在该节点内，会先安全跳回 root。
        """
        node = self.findNamedNode(nodeName)
        if node is None:
            return False

        current = self._current
        while current:
            if current is node:
                self.switchNode(self.root)
                break
            current = current._parent

        if node._parent:
            node._parent.removeChild(node)
        return True

    def getOrCreateFeatureBranch(self, featureName, parentName='features'):
        """
        获取或创建某个 feature 的专用父分支。

        例如 featureName='bayonet' 会生成：
            features > feature.bayonet
        同一 feature 的多个状态节点都挂在这个父分支下，
        方便控制它们之间的切换顺序。
        """
        branchName = 'feature.{}'.format(featureName)
        existed = self.findNamedNode(branchName)
        if existed:
            return existed

        parent = self.findNamedNode(parentName)
        if parent is None:
            return None

        branch = FeaturesBranch(branchName)
        parent.addChildren(branch)
        return branch

    def removeFeatureBranch(self, featureName, parentName='features'):
        """
        如果某个 feature 父分支已经空了，把它从父节点上移除。
        """
        branchName = 'feature.{}'.format(featureName)
        branch = self.findNamedNode(branchName)
        if branch is None:
            return False
        if branch.children:
            return False
        if branch._parent:
            branch._parent.removeChild(branch)
        return True

    def __getattr__(self, name):
        # 状态节点里 tree.xxx 读取 ShooterSystem 的字段/方法时转发。
        owner = self.__dict__.get('owner')
        if owner is not None and hasattr(owner, name):
            return getattr(owner, name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        # 状态节点里 tree.xxx = value 时，如果 xxx 是 ShooterSystem 的字段，
        # 写回 owner，避免写到组件实例上导致 ShooterSystem 读不到。
        if name == 'owner':
            object.__setattr__(self, name, value)
            return

        if name in self.__dict__:
            object.__setattr__(self, name, value)
            return

        owner = self.__dict__.get('owner')
        if owner is not None and hasattr(owner, name):
            setattr(owner, name, value)
            return

        object.__setattr__(self, name, value)


class PostureState:
    Idle = 'idle'
    Aiming = 'aiming'
    Sprinting = 'sprinting'
    Reloading = 'reloading'
    Firing = 'firing'
    Walking = 'walking'
    GunSmith = 'gunsmith'


class ShooterState:
    Sneaking = 0
    Idle = 1
    Moving = 2
    Jumping = 3


class FeaturesBranch(StateNode):
    """feature 分支节点。

    没有子节点时不能作为叶子状态被选中，
    避免状态机停在空的 features 分支上。
    """
    def canEnter(self, tree):
        return len(self.children) > 0


class NativeMinecraftState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.mapping.get('weaponName') is None

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        # 切回空手没有 draw，直接解除切枪锁
        tree.isSwitchingWeapon = False


class EquipAnyWeapon(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.mapping.get('weaponName') is not None

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        if previous in self.children:
            return
        weaponName = tree.mapping.get('weaponName')
        registerWeaponAnimations(tree.animEx.entityId, weaponName)

        # 切枪完成后播放新武器 draw
        if tree.pendingDrawKey:
            drawKey = tree.pendingDrawKey
            tree.currentDrawKey = drawKey
            tree.animEx.play(drawKey, replay=True)
            tree.pendingDrawKey = None
            duration = tree._getAnimDuration(tree.animEx, drawKey)
            addTimer(duration, lambda: tree._finishWeaponSwitch(tree.changeToken), False)


class FiringState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.weapon is not None and tree.weapon.isFiring

    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        # 手动枪机拉栓过程中只能被换弹打断，不能被奔跑/待机打断
        if tree.weapon.isManuallyCyclingBolt():
            return not tree.weapon.isFiring
        return not tree.weapon.isFiring or tree.player.isSprinting()
    
    def exit(self, next, tree):
        tree.weapon.firingDuration = 0

    def update(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        tree.weapon.firingDuration += tree.frameTime
        if not tree.weapon.isFiring:
            tree.finishTasks()


class SprintingState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.player.isSprinting()

    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return not getattr(self, 'exitingSprint', False) or getattr(self, 'exitReady', False)

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        tree.stopAiming()
        tree.weapon.isFiring = False
        tree.weapon.curState = GunState.Hold
        tree.weapon.shootSpread = 0
        self.exitingSprint = False
        self.exitReady = False
        self.castToken = getattr(self, 'castToken', 0) + 1
        self.exitToken = getattr(self, 'exitToken', 0) + 1
        if not tree.isSwitchingWeapon:
            self._playSprintEnter(tree)
        tree.weapon.interruptReloading()
        tree.weapon.canCycle = False

    def _playSprintEnter(self, tree):
        cast = tree.weapon.modify(stats.animSprintCast)
        sprint = tree.weapon.modify(stats.animSprint)
        token = self.castToken
        if cast:
            tree.animEx.play(cast, replay=True)
            duration = tree._getAnimDuration(tree.animEx, cast)
            if duration > 0:
                addTimer(duration, lambda token=token: self._playSprint(tree, token), False)
                return
        if sprint:
            tree.animEx.play(sprint, replay=True)

    def _playSprint(self, tree, token):
        if token != self.castToken or self.exitingSprint or not tree.player.isSprinting():
            return
        sprint = tree.weapon.modify(stats.animSprint)
        if sprint:
            tree.animEx.play(sprint, replay=True)

    def update(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        if self.exitingSprint:
            if tree.player.isSprinting():
                self.exitingSprint = False
                self.exitReady = False
                self.exitToken += 1
                self.castToken += 1
                self._playSprintEnter(tree)
            return
        if not tree.player.isSprinting():
            self._startSprintExit(tree)

    def _startSprintExit(self, tree):
        self.exitingSprint = True
        self.exitReady = False
        self.exitToken += 1
        token = self.exitToken
        swing = tree.weapon.modify(stats.animSprintSwing)
        if swing:
            tree.animEx.play(swing, replay=True)
            duration = tree._getAnimDuration(tree.animEx, swing)
            if duration > 0:
                addTimer(duration, lambda token=token: self._finishSprintExit(tree, token), False)
                return
        self._finishSprintExit(tree, token)

    def _finishSprintExit(self, tree, token):
        if token != self.exitToken:
            return
        self.exitReady = True
        tree.finishTasks()

    def exit(self, next, tree):
        tree.weapon.canCycle = True
        self.exitingSprint = False
        self.exitReady = False
        self.castToken = getattr(self, 'castToken', 0) + 1
        self.exitToken = getattr(self, 'exitToken', 0) + 1


class WalkingState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.weapon is not None and not tree.player.isSprinting() and tree.player.isMoving()

    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return not tree.weapon.isManuallyCyclingBolt()

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        if tree.weapon.curState != GunState.Cycling:
            tree.weapon.curState = GunState.Hold
        if tree.isSwitchingWeapon:
            return
        animWalk = tree.weapon.modify(stats.animWalk)
        tree.animEx.play(animWalk)

    def update(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        tree.idleDuration += tree.frameTime
        if tree.player.isSprinting() or not tree.player.isMoving():
            tree.finishTasks()

    def exit(self, next, tree):
        tree.idleDuration = 0


class ReloadingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return tree.weapon is not None and tree.weapon.curState == GunState.Reloading
    
    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        # 只要已经不在换弹状态（被打断/完成）就允许退出，避免手动枪机“装一发打一发”卡在换弹状态
        return tree.weapon.feed['canInterrupt'] or tree.weapon.curState != GunState.Reloading
    
    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        tree.weapon.shootSpread = 0
        if not tree.weapon.feed['canInterrupt']:
            tree.operation.SetCanWalkMode(False)
        # print 'Reloading'

    def exit(self, next, tree):
        tree.operation.SetCanWalkMode(True)

    def update(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        if tree.weapon is not None and tree.weapon.curState == GunState.Hold:
            tree.finishTasks()


class IdleState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        # 瞄准只是变量，不再作为独立状态，因此 Idle 不检查 aiming
        return not tree.player.isSprinting() and not tree.player.isMoving()

    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return not tree.weapon.isManuallyCyclingBolt()

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        # print 'Idle'
        # 拉栓中保持 curState=Cycling，不打断 cycleBolt 协程
        if tree.weapon.curState != GunState.Cycling:
            tree.weapon.curState = GunState.Hold

        # 切枪 draw 还没播完时，不播 hold，避免把拔枪动画顶掉
        if tree.isSwitchingWeapon:
            return

        # 如果当前正在播放的是换弹动画（feed 里的 reloadModes），就不播 hold
        for reloadMode in tree.weapon.feed.get('reloadModes', []):
            animKey = reloadMode.get('animation')
            if animKey and tree.animEx.isPlaying(animKey):
                return

        animHold = tree.weapon.modify(stats.animHold)
        if animHold:
            tree.animEx.play(animHold)

    def update(self, tree):
        tree.idleDuration += tree.frameTime
        if tree.player.isSprinting() or tree.player.isMoving():
            tree.finishTasks()

    def exit(self, next, tree):
        tree.idleDuration = 0



class GunSmithState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        # 仅允许从 Idle 进入，并且外部发起过 gunsmith 请求
        return tree.currentStateName() == PostureState.Idle and tree.gunSmithingRequested

    def canExit(self, tree):
        # type: (ShooterStateTreeComponent) -> None
        return not tree.gunSmithingRequested

    def enter(self, previous, tree):
        # type: (StateNode, ShooterStateTreeComponent) -> None
        gunsmithUi = GunSmithUi.pushScreen() # type: GunSmithUi
        tree.animEx.play(tree.weapon.handling['gunsmith'], clientOnly=True)
        def _onDestroy():
            tree.shooterVfx.postProcess.SetEnableByName('fullscreenblur', False)
            animHold = tree.weapon.modify(stats.animHold)
            tree.animEx.play(animHold, clientOnly=True)
            tree.animEx.setBlending(animHold, { 'duration': 0.2 })
            tree.gunSmithingRequested = False
            tree.finishTasks()
        setattr(gunsmithUi, '_ondestroy', _onDestroy)
        tree.shooterVfx.postProcess.SetEnableByName('fullscreenblur', True)
        gunsmithUi.onselect = lambda a, b: self.applyAttachment(tree.weapon, a, b)
        gunsmithUi.onslotselect = lambda slot: tree.shooterVfx.transitionToCamera(
            slot.get('cameraAligned', 'camera'), 0.2
        )
        from .gunClientSync import GunClientSyncSystem
        gunsmithUi.setAppearanceData(
            GunClientSyncSystem.getInstance().getAppearance()
        )
        gunsmithUi.displayAttachments(tree.weapon.slots, tree.weapon.attachments)

    def applyAttachment(self, basic, slot, attachment):
        # type: (GunBasic, dict, dict) -> None
        basic.applyAttachment(slot, attachment)
        try:
            from .gunClientSync import GunClientSyncSystem
            sync = GunClientSyncSystem.getInstance()
            sync.requestSetAttachments(
                dict(basic.attachments),
                sync.getAppearance()
            )
        except Exception as errorObject:
            pass

