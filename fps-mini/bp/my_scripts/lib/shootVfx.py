from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    LevelClient, QueryVariable, localPlayerId,
    addTimer,
    EventListener, events,
)
from ..engine.architect.math.double import alerp, lerp, clamp



yRot = QueryVariable('y_rot')
xRot = QueryVariable('x_rot')
isFirstPerson = QueryVariable('is_first_person')


@SubsystemClient
class PlayerShooterVfxSystem(ClientSubsystem):

    def onInit(self):
        self.canTick = True
        level = LevelClient.getInstance()
        self.audio = level.customAudio
        # self.postProcess = level.postProcess
        self.playerView = level.playerView
        self.cam = level.camera
        self.lastZRot = 0
        self.zRot = 0
        self.zRotAdders = {} # type: dict[str, float]

        rot = self.cam.GetCameraRotation()
        self.lastXRot = rot[0]
        self.lastYRot = rot[1]
        self.lastDx = 0
        self.lastDy = 0
        self.dx = 0
        self.dy = 0
        self.lastVSmooth = 0
        self.vSmooth = 0

    _fovScale = 1.0
    _fovScaleMul = 1.0

    isAiming = False

    @property
    def fovScale(self):
        return self._fovScale
    
    @fovScale.setter
    def fovScale(self, value):
        self.playerView.SetPlayerFovScale(value * self._fovScaleMul)
        self._fovScale = value

    @property
    def fovScaleMul(self):
        return self._fovScaleMul
    
    @fovScaleMul.setter
    def fovScaleMul(self, value):
        self.playerView.SetPlayerFovScale(value * self._fovScale)
        self._fovScaleMul = value

    def updateCamRot(self):
        cam = self.cam
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

    def onUpdate(self, dt):
        self.updateCamRot()

    def onRender(self, dt):
        t = dt * 25
        self.handleWeaponFollow(dt)
        self.handleCamZRot(t)
        self.handleCamVignette(dt * 4)
        self.handleMuzzleFlashDisappear(dt)

    def handleMuzzleFlashDisappear(self, dt):
        if self._muzzleFlashActive:
            self._muzzleFlashTimer -= dt
            if self._muzzleFlashTimer <= 0:
                self._muzzleFlashActive = False
                # self.postProcess.SetEnableByName('muzzle_flash', False)

    def handleWeaponFollow(self, dt):
        p = dt * 20
        _dx = lerp(self.lastDx, self.dx, p)
        _dy = lerp(self.lastDy, self.dy, p)
        xRot.setValue(localPlayerId(), _dx)
        yRot.setValue(localPlayerId(), _dy)
        self.lastDx = _dx
        self.lastDy = _dy

    def handleCamVignette(self, t):
        # vignetteEnabled = self.postProcess.CheckVignetteEnabled()
        # vSmooth = self.vSmooth
        # vSLerp = lerp(self.lastVSmooth, vSmooth, t)
        # self.lastVSmooth = vSLerp
        # if vSLerp > 0.01 and not vignetteEnabled:
        #     self.postProcess.SetEnableVignette(True)
        # if vSLerp < 0.01 and vignetteEnabled:
        #     self.postProcess.SetEnableVignette(False)
        # self.postProcess.SetVignetteSmoothness(vSLerp)
        # self.postProcess.SetVignetteRadius(0.8)
        pass

    def handleCamZRot(self, t):
        zRot = self.zRot
        for adder in self.zRotAdders.values():
            zRot += adder
        newZRot = alerp(self.lastZRot, zRot, t)
        self.lastZRot = newZRot
        x, y, _ = self.cam.GetCameraRotation()
        self.cam.SetCameraRotation((x, y, newZRot))

    def startAiming(self, fovScale, vSmooth=0.2):
        self.isAiming = True
        self.fovScale = fovScale
        self.vSmooth = vSmooth
        # self.postProcess.SetEnableByName('scope', True)

    def stopAiming(self):
        self.isAiming = False
        self.fovScale = 1.0
        self.vSmooth = 0.0
        # self.postProcess.SetEnableByName('scope', False)

    _muzzleFlashTimer = 0.0
    _muzzleFlashActive = False

    def shootCamVfx(self, zRot=1.5, fovScaleMul=1.03, sound=None):
        self.zRotAdders['shoot'] = zRot
        self.fovScaleMul = fovScaleMul
        sound and self.audio.PlayCustomUIMusic(sound)
        def _restore():
            self.zRotAdders['shoot'] = 0
            self.fovScaleMul = 1.0
        addTimer(0.05, _restore, False)

        # 枪口火焰：3D 空间点光源（先关再开确保参数更新）
        # self.postProcess.SetEnableByName('muzzle_flash', False)
        # self.postProcess.SetEnableByName('muzzle_flash', True)
        self._muzzleFlashTimer = 0.05
        self._muzzleFlashActive = True

    @EventListener()
    def onLocalLoaded(self, _=events.OnLocalPlayerStopLoading()):
        isFirstPerson.setValue(localPlayerId(), self.playerView.GetPerspective() == 0)

    @EventListener()
    def onPerspChange(self, ev=events.PerspChangeClientEvent()):
        isFirstPerson.setValue(localPlayerId(), ev.to == 0)

    def dropEmptyBullet(self, *args):
        pass