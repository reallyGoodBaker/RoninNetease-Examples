# -*- coding: utf-8 -*-
import copy

from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    Asset, Async, wait, localPlayerId,
    LevelClient, getOrCreateComponent,
    compClient, clientApi,
    TimerAdapter, addTimer,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent, AnimationEasingConf
from ..engine.architect.plugins.animation.enum import AnimationEasingTypes
from ..engine.architect.math.double import clamp
from ..engine.architect.fsm.stateTree.common import StateTree, StateNode
from ..engine.architect.utils.persona.client import PersonaRendererComponent, HandItemVisibility


from .shootVfx import PlayerShooterVfxSystem
from .bullet import ClientBulletSystem


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
        self.bulletFired = False
        self.boltOpend = False
        self.pressingTrigger = False
        self.curState = GunState.Hold
        self.aiming = False
        self.reloadTimer = None
        self.canCycle = True
        self.safe = False
        self.autoMode = GunAutoState.Full
        self.stun = None

    @Async
    def wait(self, sec):
        ftr = wait(sec)
        self.stun = ftr
        yield ftr
        self.stun = None


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

        if self.trigger['fireMode'] != 'burst':
            if self.bulletCount > 0 and (self.bulletFired or self.boltOpend):
                self.cycleBolt()
                return
            self.curState = GunState.Firing
            yield self.wait(self.triggerDelay)
            self.tryFireBullet()
            self.curState = GunState.Hold
            return

        burstCount = self.trigger.get('burstCount', 1)
        everySpan = self.triggerDelay / burstCount
        for _ in range(burstCount):
            yield self.wait(everySpan)
            self.tryFireBullet()
        self.curState = GunState.Hold


    def releaseTrigger(self):
        self.pressingTrigger = False


    @Async
    def cycleBolt(self):
        if self.curState in (GunState.Cycling, GunState.Reloading):
            return

        self.curState = GunState.Cycling
        animEx = self.animEx
        isManualCycle = self.bolt['cycleMode'] == 'manual'
        animLayer = isManualCycle and 'default' or 'bolt'
        aimFeature = self.features.get('aim')
        aimBoltOpen = (self.aiming and aimFeature) and aimFeature.get('boltOpenAnim') or None
        aimBoltClose = (self.aiming and aimFeature) and aimFeature.get('boltCloseAnim') or None

        if not self.boltOpend:
            animEx.play(
                aimBoltOpen or self.bolt['boltOpenAnim'],
                animLayer, clientOnly=True
            )
            yield self.wait(self.bolt['boltOpenTime'])
            self.boltOpend = True
            # 实际上子弹只会在枪机打开时抛出，不管子弹有没有被射击过
            self.bulletCount -= 1

            self.vfxSystem.dropEmptyBullet(
                self.bullet['modelAsset']['casingEntity']
            )

        isEmpty = self.bulletCount <= 0
        if not isEmpty:
            # 在有余弹的时候才会退出空弹，因为在全部子弹都退出时枪内没有上膛的子弹
            self.bulletFired = False

        if isEmpty and self.bolt['holdOpenOnEmpty']:
            # 允许空挂的时候不应该让枪机闭合
            self.curState = GunState.Hold
            return

        animEx.play(
            aimBoltClose or self.bolt['boltCloseAnim'],
            animLayer, clientOnly=True
        )
        yield self.wait(self.bolt['boltCloseTime'])
        self.boltOpend = False
        self.curState = GunState.Hold

        if not isManualCycle and not isEmpty        \
            and self.autoMode == GunAutoState.Full  \
            and self.pressingTrigger:
            self._fireBullet()


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
        level = self.handling['recoilLevel']
        if not self.aiming:
            self.vfxSystem.shootCamVfx(1 + 0.5 * level, 1.01 + 0.02 * level, self.bolt['fireSound'])
        else:
            self.vfxSystem.shootCamVfx(0.5 + 0.4 * level, 1.01 + 0.03 * level, self.bolt['fireSound'])
        self.bulletSystem.createBulletFromFacing(
            self.bullet, self.velocityModifier
        )
        shootAnim = self.aiming and self.features['aim']['shootAnim'] or self.features['shoot']['animation']
        self.animEx.play(shootAnim, replay=True, clientOnly=True, noBlending=True)
        self.bulletFired = True

        if self.bolt['cycleMode'] == 'manual':
            yield self.wait(self.bolt['shootRestoreTime'])
            if not self.canCycle:
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
        if self.reloadTimer:
            self.reloadTimer.cancel()
            self.reloadTimer = None
            self.canCycle = True


    @Async
    def reload(self):
        if self.bulletCount >= self.magazineCapacity or self.reloadTimer:
            return

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
            return

        reloadMode = self.findProperReloadMode()
        if not reloadMode:
            return

        if isManual and not self.boltOpend:
            self.animEx.play(
                self.bolt['boltOpenAnim'], clientOnly=True
            )
            yield self.wait(self.bolt['boltOpenTime'])
            self.boltOpend = True

        self.animEx.play(reloadMode['animation'], replay=True)

        def doReload():
            reloadType = reloadMode['reloadType']
            remains = count - self.fillBullet(
                bulletItemType,
                reloadType == 'replace' and self.magazineCapacity - self.bulletCount\
                    or reloadType == 'add' and 1 or reloadMode['countPerClip']
            )

            self.bulletFired = False
            self.canCycle = True

            if self.bulletCount < self.magazineCapacity and remains > 0:
                self.reloadTimer.cancel()
                self.reloadTimer = None
                self.reload()
                return

            if self.boltOpend:
                def restoreBolt():
                    self.boltOpend = False
                    self.bulletFired = False
                    self.curState = GunState.Hold

                self.animEx.play(self.bolt['boltCloseAnim'], isManual and 'default' or 'bolt', clientOnly=True)
                addTimer(self.bolt['boltCloseTime'], restoreBolt, False)

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


class ShooterState:
    Sneaking = 0
    Idle = 1
    Moving = 2
    Jumping = 3


class NativeMinecraftState(StateNode):

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        tree.banSprint(False)
        if tree.persona.hasModified():
            tree.persona.resetPlayerRenderConf()
            tree.persona.restorePlayerRootAnim()
        clientApi.HideCrossHairGUI(False)

    def exit(self, next, tree):
        # type: (StateNode, ShooterSystem) -> None
        tree.persona.shadowPlayerRootAnim('root_rot')
        clientApi.HideCrossHairGUI(True)

    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.mapping.get('weaponName') is None


class EquipAnyWeapon(StateNode):

    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.mapping.get('weaponName') is not None

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        if previous in self.children:
            return
        weaponName = tree.mapping.get('weaponName')
        tree.persona.changeRenderConf(Asset('renderResources.' + weaponName).load(True), True)
        tree.animEx.registerAnimations(Asset('animations.' + weaponName).load(True))
        for name, easingDef in Asset('easings.' + weaponName).load(True).items():
            tree.animEx.registerEasing(name, easingDef)
        tree.animEx.updateActorAnimDef()
        tree.animEx.play(tree.movementFeature['walkAnim'], replay=True, clientOnly=True)


class AimingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.aiming and tree.weapon.canOperate()
    
    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        print 'Aiming'
        tree.weapon.interruptReloading()
        tree.shooterVfx.startAiming(1 / tree.aimFeature['scale'])
        tree.animEx.play(tree.aimFeature['animation'], clientOnly=True)
        tree.weapon.aiming = True
        if tree.player.isSprinting():
            tree.aiming = False
            tree.finishTasks()
    
    def exit(self, next, tree):
        # type: (StateNode, ShooterSystem) -> None
        tree.shooterVfx.stopAiming()
        tree.weapon.aiming = False


class SprintingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.player.isSprinting()
    
    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        print 'Sprinting'
        tree.weapon.curState = GunState.Hold
        tree.animEx.play(tree.movementFeature['sprintAnim'])
        tree.weapon.interruptReloading()
        tree.weapon.canCycle = False

    def exit(self, next, tree):
        tree.weapon.canCycle = True


class ReloadingState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return tree.weapon is not None and tree.weapon.curState == GunState.Reloading
    
    def enter(self, previous, tree):
        print 'Reloading'

    def update(self, tree):
        # type: (ShooterSystem) -> None
        if tree.weapon is not None and tree.weapon.curState == GunState.Hold:
            tree.finishTasks()


class IdleState(StateNode):
    def canEnter(self, tree):
        # type: (ShooterSystem) -> None
        return not tree.aiming and not tree.player.isSprinting()

    def enter(self, previous, tree):
        # type: (StateNode, ShooterSystem) -> None
        print 'Idle'
        tree.weapon.curState = GunState.Hold
        tree.animEx.play(tree.movementFeature['walkAnim'])


@SubsystemClient
class ShooterSystem(ClientSubsystem, StateTree):

    def __init__(self, system, engine, sysName):
        ClientSubsystem.__init__(self, system, engine, sysName)
        StateTree.__init__(self, localPlayerId())


    shooterState = ShooterState.Idle
    weapon = None # type: GunBasic | None
    sprintBannedRemains = 0.0
    canSprint = True
    aiming = False
    aimingTime = 0


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
        self.createNode(AimingState, PostureState.Aiming, armedNode)
        self.createNode(SprintingState, PostureState.Sprinting, armedNode)
        self.createNode(ReloadingState, PostureState.Reloading, armedNode)
        self.createNode(IdleState, PostureState.Idle, armedNode)


    def onUpdate(self, dt):
        self.execute()


    def banSprint(self, bool=True):
        if bool: self.actorMotion.EndSprinting()
        self.canSprint = not bool
        self.operation.SetCanWalkMode(not bool)


    def handleSprintModeChange(self, dt):
        self.sprintBannedRemains = clamp(self.sprintBannedRemains - dt, 0, 1)
        if self.canSprint and self.sprintBannedRemains > 0.1:
            self.banSprint()
        else:
            self.banSprint(False)


    def recordAimingTime(self, dt):
        if self.aiming:
            self.aimingTime += dt
        else:
            self.aimingTime = 0


    def onRender(self, dt):
        self.handleSprintModeChange(dt)
        self.recordAimingTime(dt)


    def changeWeaponAsset(self, weaponName=None):
        self.mapping['weaponName'] = weaponName
        self.aiming = False
        self.switchNode(self.root)
        self.finishTasks()
        # TODO: 从物品加载
        if weaponName:
            self.weapon = GunBasic(Asset('weapons.' + weaponName))
            self.aimFeature = self.weapon.features.get('aim')
            self.movementFeature = self.weapon.features.get('movement')
            self.shootFeature = self.weapon.features.get('shoot')
            self.weapon.applyBullet(self.weapon.feed['ammoType'][0])
            for animKey in self.animEx.playing.keys():
                self.animEx.stop(animKey)


    """
    玩家操作原语
    """

    def pressTrigger(self):
        if 0 < self.aimingTime < 0.2:
            return
        if self.currentStateName() == PostureState.Sprinting:
            self.sprintBannedRemains += 0.2
        self.weapon.interruptReloading()
        self.weapon.pressTrigger()


    def startAiming(self):
        self.aiming = True
        self.weapon.aiming = True
        self.finishTasks()


    def stopAiming(self):
        self.aiming = False
        self.weapon.aiming = False
        self.weapon.curState = GunState.Hold
        self.finishTasks()


    def changeSprinting(self):
        self.finishTasks()


    def startSneaking(self):
        pass


    def stopSneaking(self):
        pass


    def jump(self):
        pass


    def reload(self):
        if self.weapon.canReload():
            self.aiming = False
            self.weapon.aiming = False
            self.sprintBannedRemains += 0.2
            self.weapon.reload()
            self.finishTasks()