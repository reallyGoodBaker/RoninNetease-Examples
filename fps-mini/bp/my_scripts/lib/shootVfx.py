from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    LevelClient, QueryVariable, localPlayerId,
    addTimer,
    EventListener, events,
    compClient,
)
from ..engine.architect.math.double import alerp, lerp, clamp
from ..engine.architect.math.mat4 import Matrix, decompose


yRot = QueryVariable('y_rot')
xRot = QueryVariable('x_rot')
isFirstPerson = QueryVariable('is_first_person')
shakeScale = QueryVariable('shake_scale')
walkScale = QueryVariable('walk_scale')
controlX = QueryVariable('control_x')
controlY = QueryVariable('control_y')
controlZ = QueryVariable('control_z')


@SubsystemClient
class PlayerShooterVfxSystem(ClientSubsystem):

    def onInit(self):
        self.canTick = True
        level = LevelClient.getInstance()
        self.localId = localPlayerId()
        self.audio = level.customAudio
        self.postProcess = level.postProcess
        self.actorRender = compClient.CreateActorRender(self.localId)
        self.attr = compClient.CreateAttr(self.localId)
        self.actorMotion = compClient.CreateActorMotion(self.localId)
        self.model = compClient.CreateModel(self.localId)
        self.playerView = level.playerView
        self.cam = level.camera
        self.lastZRot = 0
        self.zRot = 0
        self.zRotAdders = {} # type: dict[str, float]
        self.cameraShake = True
        self.animCamRot = [ 0, 0, 0 ]
        self.vSpeed = 0
        self.lastY = None
        self.posComp = compClient.CreatePos(self.localId)

        rot = self.cam.GetCameraRotation()
        self.lastXRot = rot[0]
        self.lastYRot = rot[1]
        self.lastDx = 0
        self.lastDy = 0
        self.dx = 0
        self.dy = 0
        self.lastVSmooth = 0
        self.vSmooth = 0

        self.camRot = rot

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
        x, y, _ = self.camRot
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
        self.camRot = self.cam.GetCameraRotation()
        self.handleWeaponFollow(dt)
        self.handleCamZOnCamRot()
        self.handleCamZRot(t)
        self.handleWalkShakeScale(t)
        self.handleControlZRotFromMovement(dt)
        self.handleCamVignette(dt * 4)
        self.handleMuzzleFlashDisappear(dt)
        self.handleRotFromCameraAnim()
        self.cam.SetCameraRotation(self.camRot)

    def handleRotFromCameraAnim(self):
        matData = self.actorRender.GetQueryableBoneOrientation('camera')
        if not matData:
            return
        x, y, z = decompose(Matrix.Create(matData))[1]
        y -= 180
        _x, _y, _z = self.animCamRot
        dx, dy, dz = x - _x, y - _y, z - _z
        self.animCamRot = [x, y, z]
        x, y, z = self.camRot
        self.camRot = (x + dx, y + dy, z + dz)

    def handleCamZOnCamRot(self):
        x = self.actorMotion.GetInputVector()[0] * 0.5
        self.zRotAdders['zOnRot'] = clamp(self.lastDy * 0.5 - x, -1, 1)

    def handleControlZRotFromMovement(self, dt):
        x = self.actorMotion.GetInputVector()[0] * 5
        zRot = lerp(controlZ.getValue(self.localId), x, dt * 8)
        controlZ.setValue(self.localId, zRot)

    def handleWalkShakeScale(self, t):
        _shakeScale = self.isAiming and 0.4 or 1
        _walkScale = self.attr.isEntityOnGround() and 1 or 0
        _ssLerp = lerp(shakeScale.getValue(self.localId), _shakeScale, t)
        shakeScale.setValue(self.localId, _ssLerp)
        walkScale.setValue(self.localId, lerp(walkScale.getValue(self.localId), _ssLerp * _walkScale, t))

    def handleMuzzleFlashDisappear(self, dt):
        if self._muzzleFlashActive:
            self._muzzleFlashTimer -= dt
            if self._muzzleFlashTimer <= 0:
                self._muzzleFlashActive = False
                self.postProcess.SetEnableByName('muzzle_flash', False)

    def handleWeaponFollow(self, dt):
        if self.isAiming:
            xRot.setValue(self.localId, 0)
            yRot.setValue(self.localId, 0)
            self.lastDx = 0
            self.lastDy = 0
            return

        p = dt * 20
        _dx = lerp(self.lastDx, self.dx, p)
        _dy = lerp(self.lastDy, self.dy, p)
        xRot.setValue(self.localId, _dx)
        yRot.setValue(self.localId, _dy)
        self.lastDx = _dx
        self.lastDy = _dy

    def handleCamVignette(self, t):
        vignetteEnabled = self.postProcess.CheckVignetteEnabled()
        vSmooth = self.vSmooth
        vSLerp = lerp(self.lastVSmooth, vSmooth, t)
        self.lastVSmooth = vSLerp
        if vSLerp > 0.01 and not vignetteEnabled:
            self.postProcess.SetEnableVignette(True)
        if vSLerp < 0.01 and vignetteEnabled:
            self.postProcess.SetEnableVignette(False)
        self.postProcess.SetVignetteSmoothness(vSLerp)
        self.postProcess.SetVignetteRadius(0.8)

    def handleCamZRot(self, t):
        zRot = self.zRot
        for adder in self.zRotAdders.values():
            zRot += adder
        newZRot = alerp(self.lastZRot, zRot, t)
        self.lastZRot = newZRot
        x, y, _ = self.camRot
        self.camRot = (x, y, newZRot)

    def startAiming(self, fovScale, vSmooth=0.2):
        self.isAiming = True
        self.fovScale = fovScale
        self.vSmooth = vSmooth
        self.postProcess.SetEnableByName('scope', True)

    def stopAiming(self):
        self.isAiming = False
        self.fovScale = 1.0
        self.vSmooth = 0.0
        self.postProcess.SetEnableByName('scope', False)

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
        self.postProcess.SetEnableByName('muzzle_flash', False)
        self.postProcess.SetEnableByName('muzzle_flash', True)
        self._muzzleFlashTimer = 0.05
        self._muzzleFlashActive = True

    @EventListener()
    def onLocalLoaded(self, _=events.OnLocalPlayerStopLoading()):
        isFirstPerson.setValue(self.localId, self.playerView.GetPerspective() == 0)

    @EventListener()
    def onPerspChange(self, ev=events.PerspChangeClientEvent()):
        isFirstPerson.setValue(self.localId, ev.to == 0)

    def dropEmptyBullet(self, *args):
        pass