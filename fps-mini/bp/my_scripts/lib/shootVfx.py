from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    LevelClient, QueryVariable, localPlayerId, QVector3,
    EventListener, events,
    compClient,
    Component, BaseCompClient,
    Sched,
    Query, NeC, EntityId,
    getBonePosition, createComponent,
    tup, add, mul, vec, clientApi,
    lerp as lerpv, epsilon, modulo,
    UiSubsystem, UiDef, AutoCreate, Hud,
)
from ..engine.architect.math.double import alerp, lerp, clamp, random
from ..engine.architect.math.utils import worldToViewDirection, worldToViewPoint, viewToWorld, screenSize
from ..engine.architect.math.mat4 import Matrix, decompose

from .stats import stats

# TODO: Remove these imports
from mod.client.component.posCompClient import PosComponentClient
from mod.client.component.rotCompClient import RotComponentClient
from mod.client.ui.controls.baseUIControl import BaseUIControl

import math
import random as rand

FULL_ANGLE = 360

# 玩家 client_entity scripts.scale，用于世界坐标 -> 模型单位的换算
PLAYER_SCALE = 16 / 0.9375


yRot = QueryVariable('y_rot')
xRot = QueryVariable('x_rot')
crosshairRot = QVector3('c_rot')
isFirstPerson = QueryVariable('is_first_person')
shakeScale = QueryVariable('shake_scale')
walkScale = QueryVariable('walk_scale')
controlPos = QVector3('control_pos')
modelScale = QueryVariable('model_scale', 1)
isAimingVar = QueryVariable('is_aiming', 0)


class CrosshairController(object):

    def __init__(self, panel, size):
        # type: (BaseUIControl, float) -> None
        self.panel = panel
        self.size = size
        self.top = panel.GetChildByName('top').asImage()
        self.left = panel.GetChildByName('left').asImage()
        self.bottom = panel.GetChildByName('bottom').asImage()
        self.right = panel.GetChildByName('right').asImage()
        self.images = (self.top, self.right, self.bottom, self.left)
        self.setOffset()

    def _applyFunc(self, fn):
        for img in self.images:
            fn(img)

    def setAlpha(self, alpha):
        self._applyFunc(lambda img: img.SetAlpha(alpha))

    def setVisible(self, visible):
        self._applyFunc(lambda img: img.SetVisible(visible))

    def setColor(self, color):
        self._applyFunc(lambda img: img.SetSpriteColor(color))

    def setOffset(self, offset=0):
        size = self.size
        visualSpread = offset + 2
        halfSize = size / 2
        self.top.SetPosition((-halfSize, -visualSpread - size))
        self.bottom.SetPosition((-halfSize, visualSpread))
        self.left.SetPosition((-size - visualSpread, -halfSize))
        self.right.SetPosition((visualSpread, -halfSize))


@AutoCreate
@UiDef('crosshair.main')
@Hud
class CrosshairHud(UiSubsystem):

    BASE_SIZE = 8

    def onCreate(self):
        self.cross = self.find('/cross')
        self.controller = CrosshairController(self.cross, self.BASE_SIZE)
        self.canTick = True
        self.offset = 0
        self.visualOffset = 0

    def setOffset(self, offset):
        # type: (float) -> None
        self.offset = offset

    def setAlpha(self, alpha):
        # type: (float) -> None
        """
        设置准星透明度，由 vfx 驱动。
        """
        self.controller.setAlpha(max(0.0, min(1.0, alpha)))

    def setVisible(self, visible):
        # type: (bool) -> None
        self.controller.setVisible(visible)

    def onRender(self, dt):
        t = 1 - math.exp(-20 * dt)
        self.visualOffset = lerp(self.visualOffset, self.offset, t)
        self.controller.setOffset(self.visualOffset)


@Component()
class CaseMovement(BaseCompClient):
    angulerVelocity = (0, 0)
    velocity = (0, 0, 0)
    remains = 3


@SubsystemClient
class PlayerShooterVfxSystem(ClientSubsystem):

    camTransitionDuration = 0.0
    camTotalTime = epsilon
    _crosshairAlpha = 1.0
    _crosshairVisible = False
    _recoil = (0, 0)
    _recoilControl = (0, 0)

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
        self.lastY = None
        self.posComp = compClient.CreatePos(self.localId)
        self.modelZScale = 1
        self.shootSpread = 0
        self.movementSpread = 0

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
        self._grounded = False
        self._groundedTimer = 0.0
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

    def isFirstPerson(self):
        return self.playerView.GetPerspective() == 0

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

    def applySpreadOffset(self, spreadMul):
        totalSpread = self.shootSpread + self.movementSpread
        _x, _y = (random(-1, 1), random(-1, 1))
        m = math.hypot(_x, _y)
        s = totalSpread / m
        ox, oy = _x * s * spreadMul, _y * s * spreadMul
        crx = crosshairRot.x.getValue(self.localId)
        cry = crosshairRot.y.getValue(self.localId)
        crosshairRot.x.setValue(self.localId, lerp(crx, crx - ox, 0.1))
        crosshairRot.y.setValue(self.localId, lerp(cry, cry - oy, 0.1))
        return (ox, oy)

    def decayRecoil(self, decay):
        yaw, pitch = self._recoil
        if yaw == 0 and pitch == 0:
            return
        horizontal, vertical = decay
        # 水平后坐力带方向，向 0 方向衰减
        if yaw > 0:
            yaw = max(yaw - horizontal, 0)
        elif yaw < 0:
            yaw = min(yaw + horizontal, 0)
        # 垂直后坐力只向上，直接衰减到 0
        pitch = max(pitch - vertical, 0)
        self._recoil = (yaw, pitch)

    def onRender(self, dt):
        t = 1 - math.exp(-25 * dt)
        self.dt = dt
        self.camRot = self.cam.GetCameraRotation()
        self.handleWeaponFollow(dt)
        self.handleCamZOnCamRot()
        self.handleCamZRot(t)
        self.handleWalkShakeScale(t)
        self.handlecRotZRotFromMovement(dt)
        self.handleCamVignette(1 - math.exp(-8 * dt))
        self.handleMuzzleFlashDisappear(dt)
        self.handleRotFromCameraAnim(dt)
        self.handleRecoil(dt)
        self.cam.SetCameraRotation(self.camRot)
        self.handleModelZScale()
        self.handleCrosshairAlpha()
        self.handleCrosshairSpread()
        self.handleCrosshairRotRestore(dt)

    def handleCrosshairRotRestore(self, dt):
        t = 1 - math.exp(-10 * dt)
        rot = crosshairRot.getValue(self.localId)
        x, y = rot.x, rot.y
        crosshairRot.x.setValue(self.localId, lerp(x, 0, t))
        crosshairRot.y.setValue(self.localId, lerp(y, 0, t))

    def handleCrosshairSpread(self):
        crosshair = CrosshairHud.getInstance()
        if not crosshair: return
        fov = math.radians(self.cam.GetFov() * self.fovScale)
        spread = self.movementSpread + self.shootSpread
        offset = screenSize()[1] / (2 * math.tan(fov / 2)) * math.tan(math.radians(spread))
        crosshair.setOffset(offset)

    def handleRecoil(self, dt):
        x, y, z = self.camRot
        yaw, pitch = self._recoil
        # 指数平滑，避免后坐力表现随帧率变化
        alpha = 1.0 - math.exp(-dt / 0.04)
        self.camRot = (
            lerp(x, x - pitch, alpha),
            lerp(y, y + yaw, alpha),
            z
        )

    def handleModelZScale(self):
        tau = max(self.camTotalTime / 5.0, epsilon)
        alpha = 1.0 - math.exp(-self.dt / tau)
        modelScale.setValue(self.localId, lerp(
            modelScale.getValue(self.localId),
            self.modelZScale,
            alpha,
        ))

    def handleCrosshairAlpha(self):
        # vfx 驱动 crosshair 透明度，和瞄准状态耦合
        targetAlpha = 0.0 if self.isAiming and self.isFirstPerson() else 0.7
        tau = max(self.camTotalTime / 5.0, epsilon)
        alphaFactor = 1.0 - math.exp(-self.dt / tau)
        self._crosshairAlpha += (targetAlpha - self._crosshairAlpha) * alphaFactor
        crosshair = CrosshairHud.getInstance()
        if crosshair is not None:
            # 只有手持模组武器时才显示；原版物品不显示
            crosshair.setVisible(self._crosshairVisible)
            crosshair.setAlpha(self._crosshairAlpha)

    def setCrosshairVisible(self, visible):
        # type: (bool) -> None
        self._crosshairVisible = bool(visible)
        crosshair = CrosshairHud.getInstance()
        if crosshair is not None:
            crosshair.setVisible(self._crosshairVisible)

    def fadeToCamera(self, dt):
        globalOffset = getBonePosition(self.localId, self.cameraAligned) - vec(self.cam.GetPosition())
        # 骨骼还没绑好时偶尔会返回巨大坐标，这一帧直接跳过，避免模型乱飞
        if modulo(globalOffset) > 16:
            return
        self.camTransitionDuration += dt
        tau = max(self.camTotalTime / 5.0, epsilon)
        alpha = 1.0 - math.exp(-dt / tau)
        offset = worldToViewDirection(globalOffset, self.cam.GetForward(), (0.0, 1.0, 0.0))
        controlPos.setValue(self.localId, lerpv(
            controlPos.getValue(self.localId),
            vec((
                offset.x * PLAYER_SCALE,
                -offset.y * PLAYER_SCALE,
                -offset.z * PLAYER_SCALE * self.modelZScale
            )),
            alpha,
        ))

    def handleRotFromCameraAnim(self, dt):
        matData = self.actorRender.GetQueryableBoneOrientation(self.cameraAligned)
        if not matData:
            return
        self.fadeToCamera(dt)
        _, rotation, scale = decompose(Matrix.Create(matData))
        x, y, z = rotation
        y -= 180
        _x, _y, _z = self.animCamRot
        dx, dy = x - _x, y - _y
        self.animCamRot = [x, y, z]
        x, y, z = self.camRot
        self.camRot = (x + dx, y + dy, z + _z)
        self.fovScaleMul = scale[0]

    def handleCamZOnCamRot(self):
        x = self.actorMotion.GetInputVector()[0] * 0.5
        self.zRotAdders['zOnRot'] = clamp(self.lastDy * 0.5 - x, -1, 1)

    def handlecRotZRotFromMovement(self, dt):
        x = self.actorMotion.GetInputVector()[0] * 5
        zRot = lerp(crosshairRot.z.getValue(self.localId), x, 1 - math.exp(-8 * dt))
        crosshairRot.z.setValue(self.localId, zRot)

    def handleWalkShakeScale(self, t):
        _shakeScale = self.isAiming and 0.4 or 1
        # 对落地状态做短时保持，避免 isEntityOnGround() 在落地瞬间反复横跳
        if self.attr.isEntityOnGround():
            self._groundedTimer = 0.25
            self._grounded = True
        elif self._groundedTimer > 0:
            self._groundedTimer -= self.dt
        else:
            self._grounded = False
        _walkScale = 1 if self._grounded else 0
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
        p = 1 - math.exp(-20 * dt)
        _dx = lerp(self.lastDx, self.dx, p)
        _dy = lerp(self.lastDy, self.dy, p)
        self.lastDx = _dx
        self.lastDy = _dy

        if not self.isAiming:
            xRot.setValue(self.localId, _dx)
            yRot.setValue(self.localId, _dy)
            return

        # 瞄准时武器本身不随鼠标晃动，xRot/yRot 置 0
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

    def startAiming(self, basic):
        self.fovScale = 1.0 / basic.modify(stats.fovScale, default=1)
        self.modelZScale = basic.modify(stats.modelScale)
        self.cameraAligned = basic.modify(stats.cameraAligned)
        self.camTransitionDuration = 0
        self.camTotalTime = basic.modify(stats.adsIn)
        self.isAiming = True
        isAimingVar.setValue(self.localId, 1)
        self.vSmooth = basic.modify(stats.vignette)
        scope = basic.modify(stats.scopeEffect)
        if scope:
            self.postProcess.SetEnableByName('scope', True)
            self.postProcess.SetParameter('scope', 'scale', scope.get('scale', 1.5))
            self.postProcess.SetParameter('scope', 'radius', scope.get('vignette', 0.5))
            self.postProcess.SetParameter('scope', 'chromaRadius', scope.get('chroma', 0.5))
            self.postProcess.SetParameter('scope', 'bendRadius', scope.get('bend', 0.5))

    def stopAiming(self, basic):
        self.cameraAligned = 'camera'
        self.isAiming = False
        isAimingVar.setValue(self.localId, 0)
        self.fovScale = 1.0
        self.vSmooth = 0.0
        self.postProcess.SetEnableByName('scope', False)
        self.modelZScale = 1
        self.camTotalTime = basic.modify(stats.adsOut)
        self.camTransitionDuration = 0

    def transitionToCamera(self, name, duration):
        self.cameraAligned = name
        self.camTransitionDuration = 0
        self.camTotalTime = duration

    _muzzleFlashTimer = 0.0
    _muzzleFlashActive = False

    def shootCamVfx(self, sound, recoil):
        sound and self.audio.PlayCustomUIMusic(sound)
        muzzle = getBonePosition(self.localId, 'muzzle')
        muzzleView = worldToViewPoint(muzzle, self.cam.GetPosition(), self.cam.GetForward(), (0.0, 1.0, 0.0))

        sunRot = self.skyRender.GetSunRot()
        sunAngle = sunRot[2]  # 第三个分量：0=正午, 90=日落/夜晚, 180=午夜, 270=日出
        dayFactor = 0.5 + 0.5 * math.cos(math.radians(sunAngle))
        dayFactor = max(0.0, min(1.0, dayFactor))
        brightness = 0.15 + 5.0 * ((1.0 - dayFactor) ** 2.0)

        muzzlePos = [muzzleView.x, muzzleView.y, muzzleView.z, brightness]

        self.postProcess.SetEnableByName('muzzle_flash', True)
        self.postProcess.SetParameter('muzzle_flash', 'muzzlePos', muzzlePos)
        self._muzzleFlashTimer = 0.05
        self._muzzleFlashActive = True

        yaw, pitch = self._recoil
        horizontal, vertical = recoil
        self._recoil = (
            yaw + horizontal * rand.choice((-1, 1)),
            pitch + vertical,
        )

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
