from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    LevelClient, QueryVariable, localPlayerId, QVector3,
    addTimer,
    EventListener, events,
    compClient,
    Component, BaseCompClient,
    Sched,
    Query, NeC, EntityId,
    getBonePosition, createComponent,
    tup, add, mul, vec, clientApi,
    lerp as lerpv, epsilon
)
from ..engine.architect.math.double import alerp, lerp, clamp, random
from ..engine.architect.math.utils import worldToViewDirection, worldToViewPoint, viewToWorld
from ..engine.architect.math.mat4 import Matrix, decompose

# TODO: Remove these imports
from mod.client.component.posCompClient import PosComponentClient
from mod.client.component.rotCompClient import RotComponentClient

import math

FULL_ANGLE = 360

# 玩家 client_entity scripts.scale，用于世界坐标 -> 模型单位的换算
PLAYER_SCALE = 16 / 0.9375


# 调试开关：True 时会把 EXTRA_VECTOR1.w 设为 999，
# 让 shader 全屏显示传入的 vec4，用来确认数据是否真的传进去了。
DEBUG_MUZZLE_VECTOR = False

yRot = QueryVariable('y_rot')
xRot = QueryVariable('x_rot')
crosshairRot = QVector3('c_rot')
isFirstPerson = QueryVariable('is_first_person')
shakeScale = QueryVariable('shake_scale')
walkScale = QueryVariable('walk_scale')
controlPos = QVector3('control_pos')
vSpeed = QueryVariable('v_speed')
modelScale = QueryVariable('model_scale', 1)


@Component()
class CaseMovement(BaseCompClient):
    angulerVelocity = (0, 0)
    velocity = (0, 0, 0)
    remains = 3


@SubsystemClient
class PlayerShooterVfxSystem(ClientSubsystem):

    aimingTransitionDuration = 0.0
    aimingTotalTime = epsilon

    def onInit(self):
        self.canTick = True
        self.dt = 0.0
        level = LevelClient.getInstance()
        self.localId = localPlayerId()
        self.audio = level.customAudio
        self.postProcess = level.postProcess
        self.skyRender = level.skyRender
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
        self.modelZScale = 1

        rot = self.cam.GetCameraRotation()
        self.lastXRot = rot[0]
        self.lastYRot = rot[1]
        self.lastDx = 0
        self.lastDy = 0
        self.dx = 0
        self.dy = 0
        self.lastVSmooth = 0
        self.vSmooth = 0
        self.cameraAligned = 'camera'

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
        self.dt = dt
        self.camRot = self.cam.GetCameraRotation()
        self.handleWeaponFollow(dt)
        self.handleCamZOnCamRot()
        self.handleCamZRot(t)
        self.handleWalkShakeScale(t)
        self.handlecRotZRotFromMovement(dt)
        self.handleCamVignette(dt * 4)
        self.handleMuzzleFlashDisappear(dt)
        self.handleRotFromCameraAnim(dt)
        self.cam.SetCameraRotation(self.camRot)
        self.handleModelZScale()

    def handleModelZScale(self):
        modelScale.setValue(self.localId, lerp(
            modelScale.getValue(self.localId),
            self.modelZScale,
            clamp(self.aimingTransitionDuration / self.aimingTotalTime, 0, 1),
        ))

    def fadeToCamera(self, dt):
        t = clamp(self.aimingTransitionDuration / self.aimingTotalTime, 0, 1)
        self.aimingTransitionDuration += dt
        globalOffset = getBonePosition(self.localId, self.cameraAligned) - vec(self.cam.GetPosition())
        offset = worldToViewDirection(globalOffset, self.cam.GetForward(), (0.0, 1.0, 0.0))
        controlPos.setValue(self.localId, lerpv(
            controlPos.getValue(self.localId),
            vec((
                offset.x * PLAYER_SCALE,
                -offset.y * PLAYER_SCALE,
                -offset.z * PLAYER_SCALE * self.modelZScale
            )),
            t,
        ))

    def handleRotFromCameraAnim(self, dt):
        matData = self.actorRender.GetQueryableBoneOrientation(self.cameraAligned)
        if not matData:
            return
        self.fadeToCamera(dt)
        x, y, z = decompose(Matrix.Create(matData))[1]
        y -= 180
        _x, _y, _z = self.animCamRot
        dx, dy = x - _x, y - _y
        self.animCamRot = [x, y, z]
        x, y, z = self.camRot
        self.camRot = (x + dx, y + dy, z + _z)

    def handleCamZOnCamRot(self):
        x = self.actorMotion.GetInputVector()[0] * 0.5
        self.zRotAdders['zOnRot'] = clamp(self.lastDy * 0.5 - x, -1, 1)

    def handlecRotZRotFromMovement(self, dt):
        x = self.actorMotion.GetInputVector()[0] * 5
        zRot = lerp(crosshairRot.z.getValue(self.localId), x, dt * 8)
        crosshairRot.z.setValue(self.localId, zRot)

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
        p = dt * 20
        _dx = lerp(self.lastDx, self.dx, p)
        _dy = lerp(self.lastDy, self.dy, p)
        self.lastDx = _dx
        self.lastDy = _dy
        if not self.isAiming:
            xRot.setValue(self.localId, _dx)
            yRot.setValue(self.localId, _dy)
            return
        xRot.setValue(self.localId, 0)
        yRot.setValue(self.localId, 0)
        crosshairRot.x.setValue(self.localId, clamp(_dx * -0.1, -1, 1))
        crosshairRot.y.setValue(self.localId, clamp(_dy * 0.1, -1, 1))

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

    def startAiming(self, aim, vSmooth=0.2):
        self.fovScale = 1 / aim['scale']
        self.modelZScale = aim['modelScale']
        self.cameraAligned = aim['camera']
        self.aimingTransitionDuration = 0
        self.aimingTotalTime = aim['ads']
        self.isAiming = True
        self.vSmooth = vSmooth
        scope = aim.get('scope_effect')
        if scope:
            self.postProcess.SetEnableByName('scope', True)
            self.postProcess.SetParameter('scope', 'scale', scope.get('scale', 1.5))
            self.postProcess.SetParameter('scope', 'radius', scope.get('vignette', 0.5))
            self.postProcess.SetParameter('scope', 'chromaRadius', scope.get('chroma', 0.5))
            self.postProcess.SetParameter('scope', 'bendRadius', scope.get('bend', 0.5))

    def stopAiming(self):
        self.cameraAligned = 'camera'
        self.isAiming = False
        self.fovScale = 1.0
        self.vSmooth = 0.0
        self.postProcess.SetEnableByName('scope', False)
        self.modelZScale = 1
        self.aimingTransitionDuration = 0

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
        # getBonePosition 拿到的是世界坐标，用 worldToViewPoint 变换到视野/相机相对坐标
        muzzle = getBonePosition(self.localId, 'muzzle')
        muzzleView = worldToViewPoint(muzzle, self.cam.GetPosition(), self.cam.GetForward(), (0.0, 1.0, 0.0))

        # 用太阳角度算提亮倍率：太阳高 -> 白天少提亮；太阳低/落下 -> 晚上多提亮
        sunRot = self.skyRender.GetSunRot()
        sunAngle = sunRot[2]  # 第三个分量：0=正午, 90=日落/夜晚, 180=午夜, 270=日出
        # 用余弦映射：正午1.0，午夜0.0，日出日落0.5
        dayFactor = 0.5 + 0.5 * math.cos(math.radians(sunAngle))
        if DEBUG_MUZZLE_VECTOR:
            brightness = 999.0
        else:
            # 用二次幂曲线：白天控制在 0.5 左右，夜晚快速拉高，午夜最强
            dayFactor = max(0.0, min(1.0, dayFactor))
            brightness = 0.15 + 5.0 * ((1.0 - dayFactor) ** 2.0)

        muzzlePos = [muzzleView.x, muzzleView.y, muzzleView.z, brightness]

        self.postProcess.SetEnableByName('muzzle_flash', False)
        self.postProcess.SetEnableByName('muzzle_flash', True)

        # 先开启后处理再传参数，避免 enable 时重置参数
        self.postProcess.SetParameter('muzzle_flash', 'muzzlePos', muzzlePos)
        self._muzzleFlashTimer = 0.05
        self._muzzleFlashActive = True

    @EventListener()
    def onLocalLoaded(self, _=events.OnLocalPlayerStopLoading()):
        isFirstPerson.setValue(self.localId, self.playerView.GetPerspective() == 0)

    @EventListener()
    def onPerspChange(self, ev=events.PerspChangeClientEvent()):
        isFirstPerson.setValue(self.localId, ev.to == 0)

    def dropEmptyBullet(self, model, viewMotion):
        x, y, z = tup(getBonePosition(self.localId, 'ejection'))
        entityId = self.spawnEntity(
            model,
            (x, y - 64, z),
            clientApi.GetRotFromDir(self.cam.GetCameraRotation())
        )
        if not entityId:
            return
        caseMovement = createComponent(entityId, CaseMovement) # type: CaseMovement
        caseMovement.velocity = tup(add(
            viewToWorld(vec(viewMotion), self.cam.GetForward(), (0.0, 1.0, 0.0)),
            mul(vec(self.actorMotion.GetMotion()), 16)
        ))
        randomV = random(2 * FULL_ANGLE, 5 * FULL_ANGLE)
        caseMovement.angulerVelocity = (randomV, randomV / 2)

    @Sched.Render()
    @Query(EntityId, CaseMovement, NeC.Pos, NeC.Rot)
    def handleCaseMovement(self, id, movement, pos, rot):
        # type: (str, CaseMovement, PosComponentClient, RotComponentClient) -> None
        if movement.remains <= 0:
            self.destroyEntity(id)
            return
        dt = self.dt
        vx, vy, vz = movement.velocity
        movement.velocity = (vx, vy - dt * 12, vz)
        movement.remains -= dt
        pos.SetPosForClientEntity(tup(add(mul(vec(movement.velocity), dt), vec(pos.GetPos()))))
        avx, avy = movement.angulerVelocity
        rx, ry = rot.GetRot()
        rot.SetRotForClientEntity((
            rx + avx * dt, ry + avy * dt
        ))
