from ..lib.shooter import ShooterSystem
from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    EventListener, events,
    getOrCreateComponent, BaseCompClient, Component,
    Sched, Query, EntityId,
    compClient, localPlayerId,
)

from ..engine.architect.math.utils import facing
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..assets.animMeta import AnimMeta
from ..lib.render import WeaponRenderSystem
from ..lib.gunClientSync import GunClientSyncSystem
from ..engine.architect.plugins.motion.playerMotionComp import PlayerMotionComponent

from mod.common.minecraftEnum import KeyBoardType


from ..lib.gunSync import getGunItemNames


@SubsystemClient
class PlayerShooterInitSystem(ClientSubsystem):

    isMainhandAny = False

    def onInit(self):
        self.canTick = True

    def onReady(self):
        self.shooter = ShooterSystem.getInstance()
        self.renderSystem = WeaponRenderSystem.getInstance()
        animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)
        self.animEx = animEx
        animEx.registerMetadatas(AnimMeta)
        WeaponRenderSystem.registerAssetMapping(getGunItemNames())

    def changeWeapon(self, itemDict=None):
        cam = compClient.CreateCamera(localPlayerId())
        if not itemDict:
            self.isMainhandAny = False
            self.shooter.changeWeapon(None)
            cam.SetCameraOffset((0, 0, 0))
        else:
            weaponMapping = getGunItemNames()
            WeaponRenderSystem.registerAssetMapping(weaponMapping)
            itemName = itemDict.get('newItemName') or itemDict.get('itemName')
            asset = weaponMapping.get(itemName)
            ammoCount = None
            serverReady = False
            uid = ''
            # Do not render the gun until the server state has arrived.
            # PlayerShooterInitSystem no longer trusts any client-side cache.
            self.shooter.changeWeapon(asset, itemName, serverReady, ammoCount, uid)
            self.isMainhandAny = bool(asset)
            cam.SetCameraOffset((1, -0.2, -0.5))
        self.shooter.shooterVfx.setCrosshairVisible(self.isMainhandAny)

    @EventListener()
    def onLocalPlayerLoaded(self, _=events.OnLocalPlayerStopLoading()):
        self.shooter.resetSessionCache()
        GunClientSyncSystem.getInstance().syncCurrentCarried()
        itemComp = compClient.CreateItem(localPlayerId())
        itemDict = itemComp.GetCarriedItem()
        self.changeWeapon(itemDict)

    @EventListener()
    def onCarriedItemChanged(self, ev=events.OnCarriedNewItemChangedClientEvent()):
        GunClientSyncSystem.getInstance().syncCurrentCarried()
        self.changeWeapon(ev.itemDict)

    @EventListener()
    def onLeft(self, ev=events.LeftClickBeforeClientEvent()):
        if self.isMainhandAny:
            self.shooter.pressTrigger()

    @EventListener()
    def onLeftRelease(self, ev=events.LeftClickReleaseClientEvent()):
        if self.isMainhandAny:
            self.shooter.releaseTrigger()

    @EventListener()
    def onAim(self, ev=events.RightClickBeforeClientEvent()):
        if self.isMainhandAny:
            self.shooter.startAiming()

    @EventListener()
    def onAimStop(self, ev=events.RightClickReleaseClientEvent()):
        if self.isMainhandAny:
            self.shooter.stopAiming()

    @EventListener()
    def onPressKeyboard(self, ev=events.OnKeyPressInGame()):
        if not self.isMainhandAny:
            return

        isDown = ev.isDown == '1'
        if ev.key == '82' and isDown:
            self.shooter.reload()
            return
        if ev.key == '72' and isDown:
            self.shooter.startGunSmith()
            return

    @EventListener()
    def onPlayerAction(self, ev=events.OnLocalPlayerActionClientEvent()):
        if not self.isMainhandAny:
            return

        if ev.actionType == 9 or ev.actionType == 10:
            self.shooter.changeSprinting()
