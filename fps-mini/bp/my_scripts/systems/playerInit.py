from ..lib.shooter import ShooterSystem
from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    EventListener, events,
    getOrCreateComponent, localPlayerId,
)

from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..assets.animMeta import AnimMeta


WeaponMapping = {
    'roninexample:pistol': 'pistol',
    'roninexample:bolt': 'bolt',

}

@SubsystemClient
class PlayerInitSystem(ClientSubsystem):

    def onReady(self):
        self.shooter = ShooterSystem.getInstance()
        animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)
        animEx.registerMetadatas(AnimMeta)

    @EventListener()
    def onCarriedItemChanged(self, ev=events.OnCarriedNewItemChangedClientEvent()):
        itemName = ev.itemDict['newItemName']
        asset = WeaponMapping.get(itemName)
        self.shooter.changeWeaponAsset(asset)

    @EventListener()
    def onLeft(self, ev=events.LeftClickBeforeClientEvent()):
        self.shooter.pressTrigger()

    @EventListener()
    def onAim(self, ev=events.RightClickBeforeClientEvent()):
        self.shooter.startAiming()

    @EventListener()
    def onAimStop(self, ev=events.RightClickReleaseClientEvent()):
        self.shooter.stopAiming()

    @EventListener()
    def onPressKeyboard(self, ev=events.OnKeyPressInGame()):
        if ev.isDown == '0':
            return
        if ev.key == '82':
            self.shooter.reload()

    @EventListener()
    def onPlayerAction(self, ev=events.OnLocalPlayerActionClientEvent()):
        if ev.actionType == 9 or ev.actionType == 10:
            self.shooter.changeSprinting()