# -*- coding: utf-8 -*-
from ..engine.architect.compact import (
    SubsystemClient, ClientSubsystem,
    CustomEvent, EventListener, events,
    getOrCreateComponent, SubsystemManager,
    Asset, localPlayerId,
    LevelClient,
    UiDef, Hud, AutoCreate, UiSubsystem,
    signal, Sink,
    QueryVariable,
    Sched,
    compClient, vec,
    addTimer,
)
from ..engine.architect.math.double import lerp, clamp
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent, AnimationEasingConf
from ..assets.animMeta import AnimMeta

from ..lib.bullet import ClientBulletSystem
from ..lib.shootVfx import PlayerShooterVfxSystem


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


yRot = QueryVariable('y_rot')
xRot = QueryVariable('x_rot')


@SubsystemClient
class PlayerAnimationSubsystem(ClientSubsystem):

    animEx = None # type: AnimationExComponent
    aiming = False

    @Sched.Tick()
    def updateCamRot(self):
        cam = self.level.camera
        x, y, _ = cam.GetCameraRotation()
        self.dx = clamp((self.lastXRot - x) * 0.3, -4, 4)
        _dy = y - self.lastYRot
        if _dy > 180:
            _dy -= 360
        elif _dy < -180:
            _dy += 360
        self.dy = clamp(_dy * 0.3, -4, 4)
        self.lastXRot = x
        self.lastYRot = y

    def onRender(self, dt):
        p = dt * 20
        _dx = lerp(self.lastDx, self.dx, p)
        _dy = lerp(self.lastDy, self.dy, p)
        xRot.setValue(localPlayerId(), _dx)
        yRot.setValue(localPlayerId(), _dy)
        self.lastDx = _dx
        self.lastDy = _dy

    def onReady(self):
        self.shooter = PlayerShooterVfxSystem.getInstance()

    def onInit(self):
        self.canTick = True
        self.level = LevelClient.getInstance()
        rot = self.level.camera.GetCameraRotation()
        self.lastXRot = rot[0]
        self.lastYRot = rot[1]
        self.lastDx = 0
        self.lastDy = 0
        self.dx = 0
        self.dy = 0
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
        for key in mapping.keys():
            self.animEx.registerEasing(key, inConf)
        self.animEx.play('fp.hold' if ammoCount() > 1 else 'fp.hold_slide_stop', replay=True, clientOnly=True)

    @EventListener()
    def onLeftClick(self, _=events.LeftClickBeforeClientEvent()):
        ammo = ammoCount()
        if ammo <= 0:
            return
        ClientBulletSystem.getInstance().createBullet(
            Asset('bullets.template').load(True), 1,
            vec(self.level.camera.GetForward()),
            vec(compClient.CreatePos(localPlayerId()).GetPos())
        )
        self.shooter.shootCamVfx()
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
        self.shooter.startAiming(0.8)

    def stopAiming(self):
        self.animEx.play('fp.hold' if ammoCount() > 1 else 'fp.hold_slide_stop', replay=True, clientOnly=True)
        self.aiming = False
        self.shooter.stopAiming()

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

    @EventListener()
    def onChangeSprinting(self, ev=events.OnLocalPlayerActionClientEvent()):
        if ev.actionType == 9:
            self.startSprint()
        elif ev.actionType == 10:
            self.stopSprint()

    def startSprint(self):
        self.animEx.play('fp.run' if ammoCount() > 0 else 'fp.run_slide_stop', replay=True, clientOnly=True)

    def stopSprint(self):
        self.animEx.play('fp.hold' if ammoCount() > 1 else 'fp.hold_slide_stop', replay=True, clientOnly=True)
