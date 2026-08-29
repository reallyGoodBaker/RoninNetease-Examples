# -*- coding: utf-8 -*-

from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    Asset, Async, wait, localPlayerId,
    LevelClient, getOrCreateComponent,
    compClient, clientApi,
    TimerAdapter, addTimer, cancelTimer,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..engine.architect.fsm.stateTree.common import StateTree, StateNode
from ..engine.architect.utils.persona.client import PersonaRendererComponent

from mod.common.minecraftEnum import OptionId


from .shootVfx import PlayerShooterVfxSystem
from .bullet import ClientBulletSystem
from .render import WeaponRenderSystem


class GunState:
    Hold = 0
    Firing = 1
    Reloading = 2
    Cycling = 3


class GunAutoState:
    Full = 0
    Semi = 1


class GunBasic(object):

    def __init__(self, asset):
        # type: (Asset) -> None
        asset = asset.duplicated()
        level = LevelClient.getInstance()
        self.cam = level.camera
        self.audio = level.customAudio
        self.animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)
        self.vfxSystem = PlayerShooterVfxSystem.getInstance()
        self.bulletSystem = ClientBulletSystem.getInstance()

        self.bolt = asset['bolt']
        self.trigger = asset['trigger']
        self.feed = asset['feed']
        self.barrel = asset['barrel']
        self.handling = asset['handling']
        self.features = asset['features']
        self.slots = asset['slots']
        self.extra = asset['extra']
        self.boltCycleMode = self.bolt['cycleMode']
        self.isFullAuto = self.trigger.get('isFullAuto')

        self.recoilX, self.recoilY = self.bolt['recoil']
        self.triggerDelay = self.trigger['delay']
        self.magazineCapacity = self.feed['magazineCapacity']
        self.velocityModifier = self.barrel['velocityModifier']
        self.maxSpread = self.barrel['maxSpread']
        self.spreadIncreasePerShot = self.barrel['spreadIncreasePerShot']
        self.speedModifier = self.handling['speedModifier']
        self.adsInTime = self.handling['adsInTime']
        self.adsOutTime = self.handling['adsOutTime']
        self.sprintToFireTime = self.handling['sprintToFireTime']

        self.bulletCount = self.magazineCapacity
        self.attachments = {}
        self.bullet = None
        self.firedCase = False
        self.boltOpend = False
        self.pressingTrigger = False
        self.isFiring = False
        self.actionToken = 0
        self.boltCloseTimer = None
        self.curState = GunState.Hold
        self.aiming = False
        self.reloadTimer = None
        self.reloadToken = 0
        self.reloadAnimKey = None
        self.reloadBuffered = False
        self.fireBuffered = False
        self.canCycle = True
        self.safe = False
        self.autoMode = self.bolt['disconnector'] in ('enable', 'switch') and GunAutoState.Semi or GunAutoState.Full
        self.stun = None

    @Async
    def wait(self, sec):
        ftr = wait(sec)
        self.stun = ftr
        yield ftr
        self.stun = None


    def isManuallyCyclingBolt(self):
        return self.boltCycleMode == 'manual' and self.curState == GunState.Cycling


    def isWaiting(self):
        return self.stun is not None


    def changeSafeState(self, bool=True):
        if self.curState == GunState.Hold:
            self.safe = bool


    def changeAutoMode(self, autoMode):
        disconnector = self.bolt['disconnector']
        if disconnector == 'switch':
            self.autoMode = autoMode
            return autoMode

        if disconnector == 'none':
            self.autoMode = GunAutoState.Full
            return GunAutoState.Full
        
        if disconnector == 'enable':
            self.autoMode = GunAutoState.Semi
            return GunAutoState.Semi


    def canOperate(self):
        return self.curState not in (GunState.Firing, GunState.Cycling) and not self.isWaiting()
    

    def canReload(self):
        return self.curState == GunState.Hold and not self.isWaiting()


    def applyBullet(self, uri):
        if not self.canOperate():
            return
        if uri in self.feed['ammoType']:
            self.bullet = Asset(uri).load(True)
            self.curState = GunState.Hold
            if not self.bolt:
                raise ValueError('Bullet should not be "None"')


    def changeFullAuto(self, fullAuto=True):
        if not self.canOperate():
            return
        self.isFullAuto = fullAuto
        self.curState = GunState.Hold


    @Async
    def pressTrigger(self):
        if not self.canOperate() or self.safe:
            return
        token = self.actionToken

        if self.trigger['fireMode'] != 'burst':
            if self.bulletCount <= 0:
                # 子弹打空后左键只播空仓/空膛音，不自动触发换弹
                self.tryFireBullet()
                return
            # firedCase 检测栓动/泵动有没有退空弹
            # boltOpend 检测是不是空挂
            if self.firedCase or self.boltOpend:
                self.cycleBolt()
                return
            self.isFiring = True
            self.curState = GunState.Firing
            yield self.wait(self.triggerDelay)
            if token != self.actionToken:
                return
            self.pressingTrigger = True
            self.tryFireBullet()
            self.curState = GunState.Hold
            return

        self.pressingTrigger = True
        self.isFiring = True
        burstCount = self.trigger.get('burstCount', 1)
        everySpan = self.triggerDelay / burstCount
        for _ in range(burstCount):
            yield self.wait(everySpan)
            if token != self.actionToken:
                return
            self.tryFireBullet()
        self.isFiring = False
        self.curState = GunState.Hold


    def releaseTrigger(self):
        self.pressingTrigger = False


    @Async
    def cycleBolt(self):
        """
        这里的manual指的是自动/半自动武器是否手动拉枪机
        """
        if self.curState in (GunState.Cycling, GunState.Reloading):
            return

        token = self.actionToken
        self.curState = GunState.Cycling
        animEx = self.animEx
        isManualCycle = self.bolt['cycleMode'] == 'manual'
        animLayer = isManualCycle and 'default' or 'bolt'

        if not self.boltOpend:
            animEx.play(
                self.bolt['boltOpenAnim'],
                animLayer, clientOnly=True
            )
            yield self.wait(self.bolt['boltOpenTime'])
            if token != self.actionToken:
                return
            self.boltOpend = True
            # 实际上子弹只会在枪机打开时抛出，不管子弹有没有被射击过
            self.dropCasing()

            # 拉栓过程中预输入了换弹：枪机一拉开就直接进入换弹，
            # 不要再闭锁后再拉开一次，避免浪费下一发。
            if self.reloadBuffered:
                self.reloadBuffered = False
                self.isFiring = False
                self.curState = GunState.Hold
                self.reload()
                return

        isEmpty = self.bulletCount <= 0
        if not isEmpty:
            # 在有余弹的时候才会退出空弹，因为在全部子弹都退出时枪内没有上膛的子弹
            self.firedCase = False

        if isEmpty and self.bolt['holdOpenOnEmpty']:
            # 允许空挂的时候不应该让枪机闭合
            self.isFiring = False
            self.curState = GunState.Hold
            if self.reloadBuffered and self.canReload():
                self.reloadBuffered = False
                self.reload()
            return

        animEx.play(
            self.bolt['boltCloseAnim'],
            animLayer, clientOnly=True
        )
        yield self.wait(self.bolt['boltCloseTime'])
        if token != self.actionToken:
            return
        self.boltOpend = False
        self.curState = GunState.Hold

        # 如果拉栓/闭锁过程中预输入了换弹，闭锁完成后进入换弹
        if self.reloadBuffered and self.canReload():
            self.reloadBuffered = False
            self.isFiring = False
            self.reload()
            return

        if not isManualCycle and not isEmpty        \
            and self.autoMode == GunAutoState.Full  \
            and self.pressingTrigger:
            self._fireBullet()
        else:
            self.isFiring = False


    @Async
    def tryFireBullet(self):
        if self.bulletCount <= 0:
            emptyFireSound = self.bolt['emptyFireSound']
            emptyFireSound and self.audio.PlayCustomUIMusic(emptyFireSound)
            return False
        self._fireBullet()
        return True


    @Async
    def _fireBullet(self):
        # TODO: shoot bullet
        self.interruptReloading()
        self.isFiring = True
        token = self.actionToken
        level = self.handling['recoilLevel']
        if not self.aiming:
            self.vfxSystem.shootCamVfx(1 + 0.5 * level, 1.01 + 0.02 * level, self.bolt['fireSound'])
        else:
            self.vfxSystem.shootCamVfx(0.5 + 0.4 * level, 1.01 + 0.03 * level, self.bolt['fireSound'])
        self.bulletSystem.createBulletFromFacing(
            self.bullet, self.velocityModifier
        )
        self.animEx.play(self.features['shoot']['animation'], replay=True, clientOnly=True, noBlending=True)
        self.firedCase = True

        if self.bolt['cycleMode'] == 'manual':
            yield self.wait(self.bolt['shootRestoreTime'])
            if token != self.actionToken:
                self.isFiring = False
                return
            if not self.canCycle:
                self.isFiring = False
                return

        self.cycleBolt()


    def findAmmoCountInInv(self, itemType):
        # TODO: 返回背包中具体的子弹数量
        return 50
    

    def consumeBullets(self, itemType, count):
        # TODO: 消耗count个子弹，但有可能背包没这么多子弹，所以消耗后返回具体消耗数量
        return count
    

    def fillBullet(self, itemType, count):
        consumed = self.consumeBullets(itemType, count)
        self.bulletCount += consumed
        return consumed


    def interruptReloading(self):
        self.reloadToken += 1
        self.fireBuffered = False
        if self.reloadTimer:
            self.reloadTimer.cancel()
            self.reloadTimer = None
        if self.reloadAnimKey:
            self.animEx.stop(self.reloadAnimKey)
            self.reloadAnimKey = None
        self.canCycle = True
        if self.curState == GunState.Reloading:
            self.curState = GunState.Hold


    def cancelAll(self):
        # 取消旧武器所有异步协程/定时器，避免切枪后残留逻辑覆盖新武器 draw
        self.actionToken += 1
        self.interruptReloading()
        if self.boltCloseTimer:
            cancelTimer(self.boltCloseTimer)
            self.boltCloseTimer = None
        self.isFiring = False
        self.pressingTrigger = False
        self.stun = None
        self.curState = GunState.Hold


    def shouldUseCupPortBoltOpen(self):
        return not self.firedCase and self.bulletCount
    

    def dropCasing(self):
        self.firedCase = False
        if self.bulletCount > 0:
            self.bulletCount -= 1
            self.vfxSystem.dropEmptyBullet(
                self.bullet['modelAsset']['casingEntity'],
                self.bolt['ejectVelocity']
            )


    @Async
    def reload(self):
        if self.bulletCount >= self.magazineCapacity or self.reloadTimer:
            return

        self.reloadToken += 1
        token = self.reloadToken
        self.reloadBuffered = False
        self.fireBuffered = False
        self.isFiring = False
        self.canCycle = False
        self.curState = GunState.Reloading
        count = 0
        bulletItemType = self.bullet.get('itemType')
        isManual = self.bolt['cycleMode'] == 'manual'

        for ammoAssetId in self.feed['ammoType']:
            ammoId = Asset(ammoAssetId).load(True)['itemType']
            if ammoId != bulletItemType:
                continue
            count = self.findAmmoCountInInv(ammoId)
            if count > 0:
                break
        if count <= 0:
            self.canCycle = True
            self.curState = GunState.Hold
            return

        reloadMode = self.findProperReloadMode()
        if not reloadMode:
            self.canCycle = True
            self.curState = GunState.Hold
            return

        if isManual and not self.boltOpend:
            shouldUseCupPortBoltOpen = self.shouldUseCupPortBoltOpen()
            self.animEx.play(
                shouldUseCupPortBoltOpen                \
                    and self.bolt['cuppedPortOpenBolt'] \
                    or self.bolt['boltOpenAnim'],
                clientOnly=True
            )
            yield self.wait(
                shouldUseCupPortBoltOpen                \
                    and self.bolt['cuppedPortOpenTime'] \
                    or self.bolt['boltOpenTime']
            )
            if token != self.reloadToken:
                return
            self.boltOpend = True
            shouldUseCupPortBoltOpen or self.dropCasing()

        self.reloadAnimKey = reloadMode['animation']
        self.animEx.play(reloadMode['animation'], replay=True)

        def doReload():
            if token != self.reloadToken:
                return
            if self.reloadTimer:
                self.reloadTimer.cancel()
                self.reloadTimer = None
            self.reloadAnimKey = None

            reloadType = reloadMode['reloadType']
            remains = count - self.fillBullet(
                bulletItemType,
                reloadType == 'replace' and self.magazineCapacity - self.bulletCount\
                    or reloadType == 'add' and 1 or reloadMode['countPerClip']
            )
            self.canCycle = True

            # 玩家预输入了射击：装完当前这个阶段就打断后续装填
            if self.fireBuffered and isManual:
                self.fireBuffered = False
                if self.boltOpend:
                    def restoreBoltAndFire():
                        self.fireBuffered = False
                        self.boltOpend = False
                        self.firedCase = False
                        self.curState = GunState.Firing
                        self.tryFireBullet()
                    self.animEx.play(self.bolt['boltCloseAnim'], isManual and 'default' or 'bolt', clientOnly=True)
                    self.boltCloseTimer = addTimer(self.bolt['boltCloseTime'], restoreBoltAndFire, False)
                else:
                    self.curState = GunState.Firing
                    self.tryFireBullet()
                return

            if self.bulletCount < self.magazineCapacity and remains > 0:
                self.reload()
                return

            if self.boltOpend:
                def restoreBolt():
                    self.boltOpend = False
                    self.firedCase = False
                    self.curState = GunState.Hold

                self.animEx.play(self.bolt['boltCloseAnim'], isManual and 'default' or 'bolt', clientOnly=True)
                self.boltCloseTimer = addTimer(self.bolt['boltCloseTime'], restoreBolt, False)
            else:
                self.curState = GunState.Hold

        self.reloadTimer = TimerAdapter(reloadMode['reloadTime'], doReload, False)
        self.reloadTimer.start()


    def findProperReloadMode(self):
        remains = self.bulletCount
        capacity = self.magazineCapacity
        for mode in self.feed['reloadModes']:
            condition = mode['condition']
            if remains == 0 and condition == 'empty':
                return mode
            if 0 < remains < capacity and condition == 'not_full':
                return mode
            if condition == 'clip_available':
                countPerClip = mode['countPerClip']
                if capacity - remains >= countPerClip and capacity > countPerClip:
                    return mode
        return None





class PostureState:
    Idle = 'idle'
    Aiming = 'aiming'
    Sprinting = 'sprinting'
    Reloading = 'reloading'
    Firing = 'firing'


class ShooterState:
    Sneaking = 0
    Idle = 1
    Moving = 2
    Jumping = 3


class NativeMinecraftState(StateNode):

    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.mapping.get('weaponName') is None

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        # 切回空手没有 draw，直接解除切枪锁
        tree.isSwitchingWeapon = False


class EquipAnyWeapon(StateNode):

    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.mapping.get('weaponName') is not None

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        if previous in self.children:
            return
        weaponName = tree.mapping.get('weaponName')
        tree.animEx.clearRegisteredAnimations()
        tree.animEx.registerAnimations(Asset('animations.' + weaponName).load(True))
        for name, easingDef in Asset('easings.' + weaponName).load(True).items():
            tree.animEx.registerEasing(name, easingDef)
        tree.animEx.updateActorAnimDef()

        # 切枪完成后播放新武器 draw
        if tree.pendingDrawKey:
            drawKey = tree.pendingDrawKey
            tree.currentDrawKey = drawKey
            tree.animEx.play(drawKey, replay=True, clientOnly=True)
            tree.pendingDrawKey = None
            duration = tree._getAnimDuration(tree.animEx, drawKey)
            addTimer(duration, lambda: tree._finishWeaponSwitch(tree.changeToken), False)


class FiringState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.weapon is not None and tree.weapon.isFiring

    def canExit(self, tree):
        # type: (ShooterSystem) -> None
        # 手动枪机拉栓过程中只能被换弹打断，不能被奔跑/待机打断
        if tree.weapon.isManuallyCyclingBolt():
            return not tree.weapon.isFiring
        return not tree.weapon.isFiring or tree.player.isSprinting()

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        pass

    def exit(self, next, tree):
        # type: (StateNode, ShooterSystem) -> None
        pass

    def update(self, tree):
        # type: (ShooterSystem) -> None
        if not tree.weapon.isFiring:
            tree.finishTasks()


class SprintingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.player.isSprinting()
    
    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        # print 'Sprinting'
        tree.stopAiming()
        tree.weapon.isFiring = False
        tree.weapon.curState = GunState.Hold
        # 切枪 draw 还没播完时，不播奔跑动画，避免把拔枪动画顶掉
        if not tree.isSwitchingWeapon:
            tree.animEx.play(tree.movementFeature['sprintAnim'])
        tree.weapon.interruptReloading()
        tree.weapon.canCycle = False

    def exit(self, next, tree):
        tree.weapon.canCycle = True


class ReloadingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.weapon is not None and tree.weapon.curState == GunState.Reloading
    
    def canExit(self, tree):
        # type: (ShooterSystem) -> None
        # 只要已经不在换弹状态（被打断/完成）就允许退出，避免手动枪机“装一发打一发”卡在换弹状态
        return tree.weapon.feed['canInterrupt'] or tree.weapon.curState != GunState.Reloading
    
    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        if not tree.weapon.feed['canInterrupt']:
            tree.operation.SetCanWalkMode(False)
        # print 'Reloading'

    def exit(self, next, tree):
        tree.operation.SetCanWalkMode(True)

    def update(self, tree):
        # type: (ShooterSystem) -> None
        if tree.weapon is not None and tree.weapon.curState == GunState.Hold:
            tree.finishTasks()


class IdleState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        # 瞄准只是变量，不再作为独立状态，因此 Idle 不检查 aiming
        return not tree.player.isSprinting()
    
    def canExit(self, tree):
        # type: (ShooterSystem) -> None
        return not tree.weapon.isManuallyCyclingBolt()

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
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

        tree.animEx.play(tree.movementFeature['walkAnim'])


@SubsystemClient
class ShooterSystem(ClientSubsystem, StateTree):

    def __init__(self, system, engine, sysName):
        ClientSubsystem.__init__(self, system, engine, sysName)
        StateTree.__init__(self, localPlayerId())


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


    def resetContext(self):
        self.switchNode(self.root)
        self.aiming = False


    def onInit(self):
        self.canTick = True
        level = LevelClient.getInstance()
        localId = localPlayerId()

        self.operation = level.operation
        self.playerView = level.playerView
        self.actorMotion = compClient.CreateActorMotion(localId)
        self.player = compClient.CreatePlayer(localId)
        self.persona = getOrCreateComponent(localId, PersonaRendererComponent)
        self.animEx = getOrCreateComponent(localId, AnimationExComponent)


    def onReady(self):
        self.shooterVfx = PlayerShooterVfxSystem.getInstance()
        self.bullets = ClientBulletSystem.getInstance()

        self.createNode(NativeMinecraftState, 'native')
        armedNode = self.createNode(EquipAnyWeapon, 'armed') # type: EquipAnyWeapon
        self.createNode(SprintingState, PostureState.Sprinting, armedNode)
        self.createNode(ReloadingState, PostureState.Reloading, armedNode)
        self.createNode(FiringState, PostureState.Firing, armedNode)
        self.createNode(IdleState, PostureState.Idle, armedNode)


    def recordAimingTime(self, dt):
        if self.aiming:
            self.aimingTime += dt
        else:
            self.aimingTime = 0


    def onRender(self, dt):
        # 异步触发的换弹/射击没有经过 ShooterSystem 主动调用，这里补一次状态机刷新
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


    def changeWeapon(self, weaponName=None):
        # 已经在切枪流程中
        if self.isSwitchingWeapon:
            if self.switchPhase in ('holster', 'draw_reverse'):
                # holster / 反向 draw 途中再次切枪：不重新播，只更新目标武器
                self.pendingWeaponName = weaponName
                return
            if self.switchPhase == 'draw':
                self._interruptDrawSwitch(weaponName)
                return

        self.changeToken += 1
        token = self.changeToken
        self.isSwitchingWeapon = True
        self.switchPhase = 'holster'
        self.pendingWeaponName = weaponName
        self.currentDrawKey = None

        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            self.weapon.cancelAll()
        self.shooterVfx.stopAiming()

        oldWeapon = self.weapon
        holsterKey = None
        if oldWeapon:
            holsterKey = oldWeapon.features.get('movement', {}).get('holster')

        # 旧武器先播 holster，播完再切渲染资源和 draw
        if oldWeapon and holsterKey:
            oldWeapon.animEx.play(holsterKey, replay=True, clientOnly=True)
            duration = self._getAnimDuration(oldWeapon.animEx, holsterKey)
            addTimer(duration, lambda: self._finishChangeWeapon(self.pendingWeaponName, token), False)
            return

        self._finishChangeWeapon(weaponName, token)


    def _interruptDrawSwitch(self, weaponName):
        # 当前正在播 draw，再次切枪：反向播放当前 draw，然后切到新武器
        self.changeToken += 1
        token = self.changeToken
        self.pendingWeaponName = weaponName

        drawKey = self.currentDrawKey
        progress = 0.0
        if drawKey:
            info = self.animEx.getPlayingAnimation(drawKey)
            if info:
                progress = info.playTime
            self.animEx.stop(drawKey, clientOnly=True)

        if progress > 0.01:
            self.switchPhase = 'draw_reverse'
            self.animEx.play(drawKey, replay=True, playRate=-1, startOffset=progress, clientOnly=True)
            addTimer(progress, lambda: self._finishChangeWeapon(self.pendingWeaponName, token), False)
            return

        self._finishChangeWeapon(weaponName, token)


    def _finishChangeWeapon(self, weaponName, token):
        if token != self.changeToken:
            return

        self.mapping['weaponName'] = weaponName
        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            self.weapon.cancelAll()
        self.shooterVfx.stopAiming()

        # 卸载旧武器动画注册
        self.animEx.clearRegisteredAnimations()
        isCarriedAny = bool(weaponName)
        clientApi.HideCrossHairGUI(isCarriedAny)
        self.playerView.SetToggleOption(OptionId.VIEW_BOBBING, not isCarriedAny)

        renderSystem = WeaponRenderSystem.getInstance()
        if weaponName:
            self.weapon = GunBasic(Asset('weapons.' + weaponName))
            self.aimFeature = self.weapon.features.get('aim')
            self.movementFeature = self.weapon.features.get('movement')
            self.shootFeature = self.weapon.features.get('shoot')
            self.weapon.applyBullet(self.weapon.feed['ammoType'][0])
            self.pendingDrawKey = self.movementFeature.get('draw')
            if not self.pendingDrawKey:
                self.isSwitchingWeapon = False
                self.switchPhase = None
                self.currentDrawKey = None
            else:
                self.switchPhase = 'draw'
                self.currentDrawKey = None
            # 本地立即换渲染资源，同时通知服务器同步给其他客户端
            renderSystem.changeRenderResource(localPlayerId(), weaponName)
            renderSystem.sendServer('renderResource', { 'entity': localPlayerId(), 'uri': weaponName })
        else:
            self.weapon = None
            self.aimFeature = None
            self.movementFeature = None
            self.shootFeature = None
            self.pendingDrawKey = None
            self.currentDrawKey = None
            self.switchPhase = None
            self.isSwitchingWeapon = False
            renderSystem.changeRenderResource(localPlayerId(), None)
            renderSystem.sendServer('renderResource', { 'entity': localPlayerId(), 'uri': None })

        self.switchNode(self.root)
        self.finishTasks()


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
                and self.movementFeature:
            self.animEx.play(self.movementFeature['sprintAnim'])


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
        if not self.weapon or not self.aimFeature:
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
        self.shooterVfx.startAiming(self.aimFeature)


    def stopAiming(self):
        if self.isSwitchingWeapon:
            return
        self.aiming = False
        if self.weapon:
            self.weapon.aiming = False
            # 拉栓中保留 curState=Cycling；换弹中也不能重置为 Hold
            if self.weapon.curState not in (GunState.Cycling, GunState.Reloading):
                self.weapon.curState = GunState.Hold
        self.shooterVfx.stopAiming()


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
        self.shooterVfx.stopAiming()
        if self.weapon.canReload():
            self.sprintBannedRemains += 0.2
            self.weapon.reload()
            self.finishTasks()
        else:
            # 射击/拉栓过程中按 R：记下来，等拉栓闭锁完成后自动进入换弹
            self.weapon.reloadBuffered = True