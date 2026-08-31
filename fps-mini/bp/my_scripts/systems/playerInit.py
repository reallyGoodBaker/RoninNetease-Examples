from ..lib.shooter import ShooterSystem
from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    EventListener, events,
    getOrCreateComponent, localPlayerId,
    compClient,
)

from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..assets.animMeta import AnimMeta
from ..lib.render import WeaponRenderSystem


WeaponMapping = {
    'roninexample:pistol': 'pistol',
    'roninexample:bolt': 'bolt',
    'roninexample:sniper': 'sniper',
    'roninexample:auto': 'auto',
}


@SubsystemClient
class PlayerShooterInitSystem(ClientSubsystem):

    isMainhandAny = False


    def onReady(self):
        self.shooter = ShooterSystem.getInstance()
        self.renderSystem = WeaponRenderSystem.getInstance()
        animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)
        animEx.registerMetadatas(AnimMeta)
        WeaponRenderSystem.registerAssetMapping(WeaponMapping)


    def changeWeapon(self, itemDict=None):
        if not itemDict:
            self.isMainhandAny = False
            self.shooter.changeWeapon(None)
        else:
            asset = WeaponMapping.get(itemDict['newItemName'])
            self.shooter.changeWeapon(asset)
            self.isMainhandAny = bool(asset)
        self.shooter.shooterVfx.setCrosshairVisible(self.isMainhandAny)


    @EventListener()
    def onLocalPlayerLoaded(self, _=events.OnLocalPlayerStopLoading()):
        itemComp = compClient.CreateItem(localPlayerId())
        itemDict = itemComp.GetCarriedItem()
        self.changeWeapon(itemDict)


    @EventListener()
    def onCarriedItemChanged(self, ev=events.OnCarriedNewItemChangedClientEvent()):
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

        if ev.isDown == '0':
            return
        if ev.key == '82':
            self.shooter.reload()

    @EventListener()
    def onPlayerAction(self, ev=events.OnLocalPlayerActionClientEvent()):
        if not self.isMainhandAny:
            return

        if ev.actionType == 9 or ev.actionType == 10:
            self.shooter.changeSprinting()