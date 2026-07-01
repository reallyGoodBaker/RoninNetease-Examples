from ..engine.architect.compact import (
    SubsystemClient, ClientSubsystem,
    CustomEvent, EventListener, events,
    getOrCreateComponent, SubsystemManager,
    Asset, localPlayerId,
    LevelClient,
    UiDef, Hud, AutoCreate, UiSubsystem,
    signal, Sink,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent, AnimationEasingConf, AnimationBlendingTypes
from ..assets.animMeta import AnimMeta


ammoCount, setAmmo = signal(15)

@AutoCreate
@UiDef('ammo.main')
@Hud
class AmmoTextDisplay(UiSubsystem):

    def onCreate(self):
        self.ammoText = self.find('/ammoText').asLabel()

    @Sink
    def showAmmoCount(self):
        self.ammoText.SetText('{}/15'.format(ammoCount()))


@SubsystemClient
class PlayerAnimationSubsystem(ClientSubsystem):

    animEx = None # type: AnimationExComponent
    aiming = False

    def onInit(self):
        self.level = LevelClient.getInstance()
        def reloadAmmo():
            setAmmo(15)
        manager = SubsystemManager.getInstance()
        manager.bus.register(
            'reloadAmmo', reloadAmmo
        )
        manager.bus.register(
            'stopAiming', self.stopAiming
        )

    @EventListener()
    def initPlayerAnim(self, ev=events.AddPlayerCreatedClientEvent()):
        animEx = getOrCreateComponent(ev.playerId, AnimationExComponent) # type: AnimationExComponent
        animEx.registerMetadatas(AnimMeta)
        if ev.playerId == localPlayerId():
            self.animEx = animEx

    @CustomEvent('PlayerHoldNewWeapon')
    def onPlayerTryHoldNewWeapon(self, ev):
        mapping = Asset('animations.' + ev.itemName.replace('roninexample:', '')).load(True)
        self.animEx.registerAnimations(mapping)
        self.animEx.updateActorAnimDef()
        inConf = AnimationEasingConf(1, 0.1)
        outConf = AnimationEasingConf(0, 0.1)
        for key in mapping.keys():
            self.animEx.registerEasing(key, inConf, outConf)

        self.animEx.play('fp.hold' if ammoCount() > 1 else 'fp.hold_slide_stop', replay=True, clientOnly=True)

    @EventListener()
    def onLeftClick(self, _=events.LeftClickBeforeClientEvent()):
        ammo = ammoCount()
        if ammo <= 0:
            return
        if not self.aiming:
            self.animEx.play('fp.shoot' if ammo > 1 else 'fp.last_shoot', replay=True, clientOnly=True, noBlending=True)
            setAmmo(ammo - 1)
            return
        self.animEx.play('fp.aim_shoot' if ammo > 1 else 'fp.aim_last_shoot', replay=True, clientOnly=True, noBlending=True)
        setAmmo(ammo - 1)

    @EventListener()
    def onRightPress(self, _=events.RightClickBeforeClientEvent()):
        if ammoCount() <= 0:
            return
        self.aiming = True
        self.animEx.play('fp.aim' if ammoCount() > 1 else 'fp.aim_slide_stop', replay=True, clientOnly=True)
        self.level.playerView.SetPlayerFovScale(0.8)
        self.level.postProcess.SetEnableDepthOfField(True)
        self.level.postProcess.SetDepthOfFieldFarBlurScale(0)
        self.level.postProcess.SetDepthOfFieldNearBlurScale(15)

    def stopAiming(self):
        self.animEx.play('fp.hold' if ammoCount() > 1 else 'fp.hold_slide_stop', replay=True, clientOnly=True)
        self.level.playerView.SetPlayerFovScale(1)
        self.level.postProcess.SetEnableDepthOfField(False)
        self.aiming = False

    @EventListener()
    def onRightRelease(self, _=events.RightClickReleaseClientEvent()):
        self.stopAiming()
    
    @EventListener()
    def onPressKeyboard(self, ev=events.OnKeyPressInGame()):
        if ev.isDown == '0':
            return
        if ev.key == '82':
            self.animEx.play(
                'fp.reload' if ammoCount() > 0 else 'fp.reload_slide_stop',
                replay=True, clientOnly=True,
            )