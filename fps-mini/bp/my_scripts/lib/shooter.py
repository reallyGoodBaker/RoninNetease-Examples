# -*- coding: utf-8 -*-
import math

from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    Asset, localPlayerId,
    LevelClient, getOrCreateComponent,
    getOrCreateSingletonComponent,
    compClient, clientApi,
    addTimer,
    epsilon,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..engine.architect.utils.persona.client import PersonaRendererComponent

from mod.common.minecraftEnum import OptionId


from .gunBasic import GunBasic, GunState
from .stats import stats
from .shootVfx import PlayerShooterVfxSystem
from .bullet import ClientBulletSystem
from .render import WeaponRenderSystem
from .feature import LocalFeaturesComponent
from .stateTree import (
    ShooterStateTreeComponent,
    PostureState,
    ShooterState,
)


@SubsystemClient
class ShooterSystem(ClientSubsystem):

    def __init__(self, system, engine, sysName):
        ClientSubsystem.__init__(self, system, engine, sysName)
        self.stateTree = None


    frameTime = epsilon
    idleDuration = 0
    shooterState = ShooterState.Idle
    weapon = None # type: GunBasic | None
    sprintBannedRemains = 0.0
    aiming = False
    aimingTime = 0
    changeToken = 0
    pendingDrawKey = None
    currentDrawKey = None
    pendingWeaponName = None
    switchPhase = None
    isSwitchingWeapon = False
    gunSmithingRequested = False


    def resetContext(self):
        self.switchNode(self.root)
        self.aiming = False

    # StateTree 转发：ShooterSystem 自身不再继承 StateTree，
    # 统一把状态树 API 转发到 ShooterStateTreeComponent。
    def finishTasks(self):
        if self.stateTree:
            self.stateTree.finishTasks()

    def execute(self):
        if self.stateTree:
            self.stateTree.execute()

    def switchNode(self, node):
        if self.stateTree:
            self.stateTree.switchNode(node)

    def currentStateName(self):
        return self.stateTree.currentStateName() if self.stateTree else None

    def currentState(self):
        return self.stateTree.currentState() if self.stateTree else None

    @property
    def root(self):
        return self.stateTree.root if self.stateTree else None

    @property
    def mapping(self):
        return self.stateTree.mapping if self.stateTree else {}


    def onInit(self):
        self.canTick = True
        level = LevelClient.getInstance()
        localId = localPlayerId()

        self.operation = level.operation
        self.playerView = level.playerView
        self.actorMotion = compClient.CreateActorMotion(localId)
        self.attr = compClient.CreateAttr(localId)
        self.player = compClient.CreatePlayer(localId)
        self.persona = getOrCreateComponent(localId, PersonaRendererComponent)
        self.animEx = getOrCreateComponent(localId, AnimationExComponent)
        # The item currently bound to self.weapon; used to apply server state.
        self.currentItemName = None
        self.currentUid = ''
        # When a gun is selected but the server state has not arrived yet, keep
        # the weapon hidden until GunClientSync delivers the state.
        self.pendingServerWeaponName = None
        self.pendingServerItemName = None
        self.pendingUid = None
        self.pendingServerState = None
        self.pendingServerUid = ''


    def resetSessionCache(self):
        # type: () -> None
        """Clear client-side session cache when entering a fresh world/save."""
        self.currentItemName = None
        self.currentUid = ''
        self.pendingServerWeaponName = None
        self.pendingServerItemName = None
        self.pendingUid = None
        self.pendingServerState = None
        self.pendingServerUid = ''

    def onReady(self):
        self.shooterVfx = PlayerShooterVfxSystem.getInstance()
        self.bullets = ClientBulletSystem.getInstance()
        self.featuresComponent = getOrCreateSingletonComponent(LocalFeaturesComponent)

        # 状态树从 ShooterSystem 中拆出，放到轻量 Component 上。
        self.stateTree = getOrCreateComponent(localPlayerId(), ShooterStateTreeComponent)
        self.stateTree.bindOwner(self)

        self.stateTree.buildDefaultTree()


    def hasFeature(self, name):
        if not self.weapon:
            return False
        return self.featuresComponent.hasFeature(name)


    def recordAimingTime(self, dt):
        if self.aiming:
            self.aimingTime += dt
        else:
            self.aimingTime = 0


    def onRender(self, dt):
        # 异步触发的换弹/射击没有经过 ShooterSystem 主动调用，这里补一次状态机刷新
        self.frameTime = dt
        if self.weapon:
            if self.weapon.curState == GunState.Reloading \
                    and self.currentStateName() != PostureState.Reloading:
                self.finishTasks()
            elif self.currentStateName() == PostureState.Reloading \
                    and self.weapon.curState != GunState.Reloading:
                self.finishTasks()

            if self.weapon.isFiring \
                    and self.currentStateName() != PostureState.Firing:
                self.finishTasks()
            elif self.currentStateName() == PostureState.Firing \
                    and not self.weapon.isFiring:
                self.finishTasks()
        self.execute()
        self.recordAimingTime(dt)


    def changeWeapon(self, weaponName=None, itemName=None, serverReady=False, ammoCount=None, uid=None):
        # If the gun was selected but the server has not returned its state yet,
        # hide the weapon and wait for GunClientSyncSystem.applyServerGunState().
        if weaponName and not serverReady:
            # 如果手上已经是这把枪了，不要再 holster/draw，并清除可能存在的另一把枪的 pending
            if self.weapon and self.currentItemName == itemName:
                self.pendingServerWeaponName = None
                self.pendingServerItemName = None
                self.pendingUid = None
                self.pendingServerState = None
                self.pendingServerUid = ''
                # 如果正在切别的枪中途拐回到当前枪，取消这次切枪
                if self.isSwitchingWeapon:
                    self.changeToken += 1
                    self.isSwitchingWeapon = False
                    self.switchPhase = None
                    self.pendingWeaponName = None
                    self.pendingItemName = None
                    self.pendingAmmoCount = None
                    self.pendingUid = None
                    self.currentDrawKey = None
                return
            self.pendingServerWeaponName = weaponName
            self.pendingServerItemName = itemName
            self.pendingUid = uid
            self.changeToken += 1
            token = self.changeToken

            # 先播上一把枪的 holster，再收起武器等待服务器状态
            oldWeapon = self.weapon
            holsterKey = oldWeapon.modify(stats.animHolster) if oldWeapon else None
            if oldWeapon and holsterKey:
                self.isSwitchingWeapon = True
                self.switchPhase = 'holster'
                oldWeapon.animEx.play(holsterKey, replay=True)
                duration = self._getAnimDuration(oldWeapon.animEx, holsterKey)
                addTimer(duration, lambda: self._finishChangeWeapon(None, token, None, None), False)
            else:
                self._finishChangeWeapon(None, token, None, None)
            return

        # A real weapon switch is allowed now; clear any server-wait state.
        self.pendingServerWeaponName = None
        self.pendingServerItemName = None
        self.pendingUid = None

        # 已经在切枪流程中
        if self.isSwitchingWeapon:
            if self.switchPhase in ('holster', 'draw_reverse'):
                # holster / 反向 draw 途中再次切枪：不重新播，只更新目标武器
                self.pendingWeaponName = weaponName
                self.pendingItemName = itemName
                self.pendingAmmoCount = ammoCount
                self.pendingUid = uid
                return
            if self.switchPhase == 'draw':
                self._interruptDrawSwitch(weaponName, itemName, ammoCount, uid)
                return

        self.changeToken += 1
        token = self.changeToken
        self.isSwitchingWeapon = True
        self.switchPhase = 'holster'
        self.pendingWeaponName = weaponName
        self.pendingItemName = itemName
        self.pendingAmmoCount = ammoCount
        self.pendingUid = uid
        self.currentDrawKey = None

        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            self.weapon.cancelAll()
        self.hasFeature('aim') and self.shooterVfx.stopAiming(self.weapon)

        oldWeapon = self.weapon
        holsterKey = None
        if oldWeapon:
            holsterKey = oldWeapon.modify(stats.animHolster)

        # 旧武器先播 holster，播完再切渲染资源和 draw
        if oldWeapon and holsterKey:
            oldWeapon.animEx.play(holsterKey, replay=True)
            duration = self._getAnimDuration(oldWeapon.animEx, holsterKey)
            addTimer(duration, lambda: self._finishChangeWeapon(self.pendingWeaponName, token, self.pendingItemName, self.pendingAmmoCount, self.pendingUid), False)
            return

        self._finishChangeWeapon(weaponName, token, itemName, ammoCount, uid)


    def _interruptDrawSwitch(self, weaponName, itemName=None, ammoCount=None, uid=None):
        # 当前正在播 draw，再次切枪：反向播放当前 draw，然后切到新武器
        self.changeToken += 1
        token = self.changeToken
        self.pendingWeaponName = weaponName
        self.pendingItemName = itemName
        self.pendingAmmoCount = ammoCount
        self.pendingUid = uid

        drawKey = self.currentDrawKey
        progress = 0.0
        if drawKey:
            info = self.animEx.getPlayingAnimation(drawKey)
            if info:
                progress = info.playTime
            self.animEx.stop(drawKey)

        if progress > 0.01:
            self.switchPhase = 'draw_reverse'
            self.animEx.play(drawKey, replay=True, playRate=-1, startOffset=progress)
            addTimer(progress, lambda: self._finishChangeWeapon(self.pendingWeaponName, token, self.pendingItemName, self.pendingAmmoCount, self.pendingUid), False)
            return

        self._finishChangeWeapon(weaponName, token, itemName, ammoCount, uid)


    def _applyServerStateIfReady(self):
        # type: () -> None
        """Apply canonical server state after the new weapon is actually built."""
        from .gunClientSync import GunClientSyncSystem
        sync = GunClientSyncSystem.getInstance()
        state = sync.getCanonicalState()
        if state and state.get('itemName') == self.currentItemName:
            self.applyServerGunState(state, sync.getCurrentUid())


    def _finishChangeWeapon(self, weaponName, token, itemName=None, ammoCount=None, uid=None):
        if token != self.changeToken:
            return

        self.currentItemName = itemName
        self.currentUid = uid or ''
        self.mapping['weaponName'] = weaponName
        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            self.weapon.cancelAll()
        self.hasFeature('aim') and self.shooterVfx.stopAiming(self.weapon)

        # 卸载旧武器动画注册
        self.animEx.clearRegisteredAnimations()
        isCarriedAny = bool(weaponName)
        clientApi.HideCrossHairGUI(isCarriedAny)
        self.playerView.SetToggleOption(OptionId.VIEW_BOBBING, not isCarriedAny)

        renderSystem = WeaponRenderSystem.getInstance()
        if weaponName:
            asset = Asset('weapons.' + weaponName)
            if not self.weapon:
                self.weapon = GunBasic(asset, ammoCount)
            else:
                self.weapon.resetTo(asset, ammoCount)
            self.weapon.applyBullet(self.weapon.feed['ammoType'][0])
            self.weapon.setAmmoChangeCallback(self._onAmmoChanged)
            self._applyServerStateIfReady()
            self.pendingDrawKey = self.weapon.modify(stats.animDraw)
            if not self.pendingDrawKey:
                self.isSwitchingWeapon = False
                self.switchPhase = None
                self.currentDrawKey = None
            else:
                self.switchPhase = 'draw'
                self.currentDrawKey = None
            # 本地立即换渲染资源，同时通知服务器同步给其他客户端
            renderSystem.sendServer('renderResource', { 'entity': localPlayerId(), 'uri': weaponName })
        else:
            # 切回空手时清除枪械 feature，并摘除动态挂载的 feature 状态节点
            self.featuresComponent.clear()
            try:
                from .tint import clearAppearance
                clearAppearance()
            except Exception as errorObject:
                pass
            self.weapon = None
            self.pendingDrawKey = None
            self.currentDrawKey = None
            self.switchPhase = None
            self.isSwitchingWeapon = False
            # 先本地立即清除枪模，避免 holster 结束后剩一帧又出现
            renderSystem.changeRenderResource(localPlayerId(), None)
            renderSystem.sendServer('renderResource', { 'entity': localPlayerId(), 'uri': None })
            if self.pendingServerState:
                pendingState = self.pendingServerState
                pendingUid = self.pendingServerUid
                self.pendingServerState = None
                self.pendingServerUid = ''
                self.applyServerGunState(pendingState, pendingUid)

        self.switchNode(self.root)
        self.finishTasks()


    def _onAmmoChanged(self, ammoCount):
        # type: (int) -> None
        if not self.currentItemName or not self.currentUid:
            return
        try:
            from .gunClientSync import GunClientSyncSystem
            GunClientSyncSystem.getInstance().requestSetAmmoCount(ammoCount)
        except Exception as errorObject:
            pass


    def applyServerGunState(self, state, uid=None):
        # type: (dict, str | None) -> bool
        """Apply server-stored ammo to the currently held gun when state arrives."""
        stateItemName = state.get('itemName')
        if self.pendingServerWeaponName and self.pendingServerItemName == stateItemName:
            # 如果正在播叠上一把枪的 holster，先放入缓存，等 holster 完成后再应用
            if self.isSwitchingWeapon and self.switchPhase == 'holster':
                self.pendingServerState = state
                self.pendingServerUid = uid or ''
                return False
            weaponName = self.pendingServerWeaponName
            itemName = self.pendingServerItemName
            savedAmmo = state.get('ammoCount')
            ammoCount = savedAmmo if savedAmmo is not None and savedAmmo >= 0 else None
            self.pendingServerWeaponName = None
            self.pendingServerItemName = None
            self.changeWeapon(weaponName, itemName, True, ammoCount, uid)
            attachments = state.get('attachments')
            if isinstance(attachments, dict) and self.weapon:
                self.weapon.applyServerAttachments(attachments)
            self._applyAppearanceState(state)
            return True

        if not self.weapon:
            return False
        if stateItemName != self.currentItemName:
            return False
        if uid:
            self.currentUid = uid
        attachments = state.get('attachments')
        if isinstance(attachments, dict):
            self.weapon.applyServerAttachments(attachments)
        self._applyAppearanceState(state)

        ammoCount = state.get('ammoCount')
        if ammoCount is None or ammoCount < 0:
            return False
        capacity = self.weapon.modify(stats.magazineCapacity)
        self.weapon.bulletCount = max(0, min(capacity, int(ammoCount)))
        return True

    def _applyAppearanceState(self, state):
        # type: (dict) -> None
        from .tint import applyAppearance
        appearance = state.get('appearance')
        applyAppearance(appearance)


    def _getAnimDuration(self, animEx, animKey):
        info = animEx.getPlayingAnimation(animKey)
        if info and info.duration and info.duration < 1000:
            return info.duration
        return 0.3


    def _finishWeaponSwitch(self, token):
        if token != self.changeToken:
            return
        self.isSwitchingWeapon = False
        self.switchPhase = None
        self.currentDrawKey = None
        # 如果拔枪动画播完后玩家还在奔跑，补播奔跑动画
        if self.player.isSprinting() \
                and self.currentStateName() == PostureState.Sprinting \
                and self.hasFeature('sprint'):
            self.currentState()._playSprintEnter(self.stateTree)


    """
    玩家操作原语
    """

    def pressTrigger(self):
        # 拔枪/收枪过程中不允许射击
        if self.isSwitchingWeapon:
            return
        if 0 < self.aimingTime < 0.2:
            return
        if self.currentStateName() == PostureState.Sprinting:
            self.sprintBannedRemains += 0.2
        if self.weapon and self.weapon.curState == GunState.Reloading:
            # 换弹中预输入射击：记下来，等当前装填阶段结束再打断换弹并开枪
            self.weapon.fireBuffered = True
            return
        self.weapon.interruptReloading()
        self.weapon.pressTrigger()
        self.finishTasks()


    def releaseTrigger(self):
        if self.isSwitchingWeapon:
            return
        self.weapon.releaseTrigger()


    def startAiming(self):
        # 拔枪/收枪过程中不允许瞄准
        if self.isSwitchingWeapon:
            return
        if self.currentStateName() == PostureState.Sprinting:
            return
        if not self.weapon or not self.hasFeature('aim'):
            return
        # 换弹中不能瞄准
        if self.weapon.curState == GunState.Reloading:
            return
        # 手动枪机拉栓中不能瞄准；自动枪机允许在射击/拉栓循环中瞄准
        if self.weapon.bolt['cycleMode'] != 'auto' and self.weapon.curState == GunState.Cycling:
            return
        # 瞄准只是变量，不再作为独立状态
        self.aiming = True
        self.weapon.aiming = True
        self.shooterVfx.startAiming(self.weapon)


    def stopAiming(self):
        if not self.hasFeature('aim'):
            return
        if self.isSwitchingWeapon:
            return
        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            # 拉栓中保留 curState=Cycling；换弹中也不能重置为 Hold
            if self.weapon.curState not in (GunState.Cycling, GunState.Reloading):
                self.weapon.curState = GunState.Hold
        self.shooterVfx.stopAiming(self.weapon)


    def changeSprinting(self):
        # 拔枪/收枪过程中不允许打断切枪流程
        if self.isSwitchingWeapon:
            return
        if self.player.isSprinting():
            # 开始奔跑时直接退出瞄准，不等状态机切换
            self.stopAiming()
        self.finishTasks()


    def startSneaking(self):
        pass


    def stopSneaking(self):
        pass


    def jump(self):
        pass


    def reload(self):
        # 拔枪/收枪过程中不允许换弹
        if self.isSwitchingWeapon:
            return
        if self.player.isSprinting():
            return
        if self.weapon.curState == GunState.Reloading:
            return
        self.aiming = False
        self.weapon.aiming = False
        self.hasFeature('aim') and self.shooterVfx.stopAiming(self.weapon)
        if self.weapon.canReload():
            self.sprintBannedRemains += 0.2
            self.weapon.reload()
            self.finishTasks()
        else:
            # 射击/拉栓过程中按 R：记下来，等拉栓闭锁完成后自动进入换弹
            self.weapon.reloadBuffered = True

    def decayRecoil(self):
        decay = self.weapon.bolt['recoil']['decay']
        self.shooterVfx.decayRecoil(decay)

    def updateMovementSpread(self):
        baseSpread = not self.attr.isEntityOnGround() and 1.5 or 0
        isMoving = self.player.isMoving()
        if self.hasFeature('walk'):
            baseSpread += isMoving and self.weapon.modify(stats.walkSpread) or 0
        self.shooterVfx.movementSpread = baseSpread

    def decaySpread(self):
        decay = self.weapon.barrel['spread']['decay']
        shootSpread = max(0, self.weapon.shootSpread - decay * math.log(self.idleDuration * decay + 1))
        self.shooterVfx.shootSpread = shootSpread
        self.weapon.shootSpread = shootSpread

    def onUpdate(self, dt):
        if not self.weapon:
            return
        self.decayRecoil()
        self.updateMovementSpread()
        self.decaySpread()

    def startGunSmith(self):
        # 仅允许从 Idle 进入，避免在移动/换弹/射击/奔跑中打开改枪界面
        if self.currentStateName() != PostureState.Idle or len(self.weapon.slots) == 0:
            return
        self.gunSmithingRequested = True
        self.finishTasks()
