import time
import math

from ..engine.architect.compact import (
    Asset, remote,
    SubsystemClient, ClientSubsystem,
    LevelClient, addTimer, Sched,
    vec, modulo, Vector3, normalize, tup, mul,
    clientApi, compClient, localPlayerId,
    Curve,
)
from ..engine.architect.math.utils import entityAabbDef, pointToLineDist
from ..engine.architect.math.double import clamp
from ..engine.architect.core.configurator import modConf
from ..engine.architect.utils.enhance.list import find


class BulletBase(object):

    def create(self, asset, velocityModifier, direction, origin):
        # type: (dict, float, Vector3, Vector3) -> None
        projectile = asset['projectile']
        self.ignoreEntities = Asset(projectile['ignoreEntities']).load(True)
        self.caliber = projectile['caliber']
        self.payloads = asset['payloads']
        self.penetrate = asset['penetrate']
        self.penetrateBlocks = Asset(self.penetrate['penetrateBlocks']).load(True)
        self.destroy = asset['destroy']
        self.initialSpeed = projectile['baseSpeed'] * velocityModifier # type: float
        self.gravity = vec((0, projectile['gravity'], 0)) # type: Vector3
        self.drag = projectile['drag'] # type: float
        self.pos = origin
        self.velocity = mul(direction, self.initialSpeed) # type: Vector3
        self.speed = self.initialSpeed

        self.createTime = time.time()
        self.prevTime = self.createTime

        self.flying = True
        self.flyTime = 0
        self.distance = 0
        self.damageRemains = 1.0
        self.step = -1


    def getPayload(self, type):
        return find(self.payloads, lambda payload: payload['type'] == type)


    def update(self, clientBullet):
        # type: (ClientBulletSystem) -> None
        """
        在 ScriptTick 中使用, 而不是 RenderTick, 防止不同帧率获得不同的弹道
        """
        if not self.flying:
            return

        # 更新时间
        currentTime = time.time()
        dt = currentTime - self.prevTime
        self.prevTime = currentTime
        self.flyTime = currentTime - self.createTime
        curVelocity = self.velocity
        self.step += 1

        # 射线检测子弹命中
        self.bulletHitTest(clientBullet, self.pos, curVelocity, dt)

        # 超过最大飞行时间销毁子弹
        if self.flyTime >= self.destroy['duration']:
            self.flying = False
            return

        # 计算子弹当前位置
        moved = curVelocity * dt
        self.pos += moved
        self.distance += modulo(moved)

        # 超过最大飞行距离销毁子弹
        if self.distance >= self.destroy['distance']:
            self.flying = False
            return

        # 计算子弹速度
        lastVelocity = self.velocity + self.gravity
        lastSpeed = modulo(lastVelocity)
        dir = normalize(lastVelocity)
        speedDecay = self.drag * lastSpeed ** 2 * dt 
        if speedDecay >= lastSpeed:
            self.flying = False
        else:
            currentSpeed = lastSpeed - speedDecay
            if currentSpeed <= self.destroy['velocity']:
                self.flying = False
                return
            self.velocity = dir * currentSpeed
            self.speed = currentSpeed


    def bulletHitTest(self, clientBullet, pos, v, dt):
        # type: (ClientBulletSystem, Vector3, Vector3, float) -> None
        displacement = v * dt
        dist = modulo(displacement)
        rayCasted = clientApi.getEntitiesOrBlockFromRay(
            tup(pos), tup(normalize(displacement)),
            int(math.ceil(dist)), True, 3
        )
        if not rayCasted:
            clientBullet.updateClientVfx(pos, pos + displacement, self)
            return

        regularResults = filter(
            lambda result: modulo(vec(result['hitPos']) - pos) < dist,
            rayCasted
        )

        lastHit = None

        for result in regularResults:
            if result['type'] == 'Block':
                lastHit = result
                if self.handleHitBlock(result, clientBullet):
                    break
                continue
            if result['entityId'] == localPlayerId() or result['identifier'] in self.ignoreEntities:
                continue
            lastHit = result
            if self.handleHitEntity(result, clientBullet, normalize(v)):
                break

        clientBullet.updateClientVfx(pos, lastHit and vec(lastHit['hitPos']) or pos + displacement, self)


    def handleHitBlock(self, result, clientBullet):
        # type: (dict, ClientBulletSystem) -> bool | None
        blockType = result['identifier']
        if self.speed >= self.penetrate['minPenetrateSpeed']:
            return self.handlePenetrateBlock(blockType, result['pos'], result['hitPos'], clientBullet)
        else:
            self.flying = False
            return True


    def handleHitEntity(self, result, clientBullet, vDir):
        # type: (dict, ClientBulletSystem, Vector3) -> bool | None
        entityId = result['entityId']
        min, max = entityAabbDef(entityId)
        halfHeadHeight = (max[1] - min[1]) / 2
        radius = math.sqrt((max[0] - min[0]) ** 2 + (max[1] - min[1]) ** 2 + (max[2] - min[2]) ** 2) / 2
        x, y, z = compClient.CreateModel(entityId).GetBonePositionFromMinecraftObject('head') or (0, 0, 0)
        hitPos = result['hitPos']
        headCenterToRay = pointToLineDist(vec((x, y + halfHeadHeight, z)), vec(hitPos), vDir)
        isHeadShot = headCenterToRay <= radius

        if self.speed >= self.penetrate['minPenetrateSpeed']:
            self.handlePenetrateEntity(entityId, isHeadShot, hitPos, clientBullet)
        else:
            self.handleKineticPayload(entityId, isHeadShot, hitPos, clientBullet)
            self.flying = False
            return True


    def handlePenetrateBlock(self, typeId, pos, hitPos, clientBullet):
        # type: (str, tuple, tuple, ClientBulletSystem) -> None
        if typeId in self.penetrateBlocks:
            self.velocity *= self.penetrate['velocityRetentionPerPass']
            self.speed = modulo(self.velocity)
            clientBullet.breakBlock(pos, hitPos)
            return False
        return True
    

    def baseDamage(self, kinetic=None):
        if not kinetic:
            return 0
        return 


    def calcDamage(self, isHeadShot, kinetic, overPun=False):
        headShotMul = (kinetic['headshotMultiplier'] * int(isHeadShot)) or 1
        baseDamage = kinetic['baseDamage']
        damageMul = Asset(kinetic['damageCurve']).load(True) # type: Curve
        overpenMul = not overPun and 1 or (isHeadShot and 1 or self.penetrate['damageRetentionPerPass'])
        return baseDamage, damageMul.getValue(self.speed) * overpenMul * headShotMul


    def handlePenetrateEntity(self, entityId, isHeadShot, hitPos, clientBullet):
        # type: (str, bool, tuple, ClientBulletSystem) -> None
        self.velocity *= self.penetrate['velocityRetentionPerPass']
        self.speed = modulo(self.velocity)
        kinetic = self.getPayload('kinetic')
        if kinetic:
            clientBullet.damageEntity(entityId, isHeadShot, self.calcDamage(isHeadShot, kinetic, True), self.caliber, hitPos)


    def handleKineticPayload(self, entityId, isHeadShot, hitPos, clientBullet):
        # type: (str, bool, tuple, ClientBulletSystem) -> None
        kinetic =  self.getPayload('kinetic')
        if not kinetic:
            return
        clientBullet.damageEntity(entityId, isHeadShot, self.calcDamage(isHeadShot, kinetic), self.caliber, hitPos)



@SubsystemClient
class ClientBulletSystem(ClientSubsystem):

    def onInit(self):
        self.activeBullets = [] # type: list[BulletBase]
        self.idleBullets = [] # type: list[BulletBase]


    def onReady(self):
        self.level = LevelClient.getInstance()
        self.drawing = self.level.drawing
        self.debug = modConf()('DEBUG')


    def updateClientVfx(self, start, end, bullet):
        # type: (Vector3, Vector3, BulletBase) -> None
        if self.debug:
            self.updateDebugBulletTrail(start, end, bullet)


    def updateDebugBulletTrail(self, start, end, bullet):
        # type: (Vector3, Vector3, BulletBase) -> None
        if not bullet.step:
            return
        color = [1, 0, 0]
        if bullet.speed >= bullet.penetrate['minPenetrateSpeed']:
            color = [0, 0, 1]
        elif bullet.getPayload('kinetic'):
            _, mul = bullet.calcDamage(False, bullet.getPayload('kinetic'))
            multiplier = clamp(mul, 0, 1)
            color[1] = multiplier
            color[0] = 1 - multiplier
        shape = self.drawing.AddLineShape(
            tup(start), tup(end), tuple(color)
        )
        addTimer(1, lambda: shape.Remove(), False)


    def breakBlock(self, pos, hitPos):
        if self.debug:
            shape = self.drawing.AddSphereShape(hitPos, 1, (1, 0, 0))
            addTimer(1, lambda: shape.Remove(), False)
        remote.client.call(
            'BulletServerAuthSystem.tryBreakBlock', pos
        )


    def damageEntity(self, target, isHeadShot, damageInfo, caliber, hitPos):
        baseDamage, multiplier = damageInfo
        damage = baseDamage * multiplier
        if self.debug:
            shape = self.drawing.AddSphereShape(hitPos, 1, isHeadShot and (1, 0, 0) or (1, 1, 0))
            addTimer(1, lambda: shape.Remove(), False)
            self.level.textNotify.SetLeftCornerNotify('{} {}'.format(damage, caliber))
        remote.client.call(
            'BulletServerAuthSystem.tryDamageEntity', target, damage, caliber
        )


    def createBullet(self, asset, velocityModifier, direction, origin):
        # type: (dict, float, Vector3, Vector3) -> None
        if len(self.idleBullets):
            idleBullet = self.idleBullets.pop()
            idleBullet.create(asset, velocityModifier, direction, origin)
            self.activeBullets.append(idleBullet)
            return
        newBullet = BulletBase()
        newBullet.create(asset, velocityModifier, direction, origin)
        self.activeBullets.append(newBullet)


    def createBulletFromFacing(self, asset, velocityModifier):
        localId = localPlayerId()
        pos = vec(compClient.CreatePos(localId).GetPos())
        dir = not self.level.playerView.GetPerspective()    \
            and vec(self.level.camera.GetForward())         \
            or vec(clientApi.GetDirFromRot(compClient.CreateRot(localId)))
        self.createBullet(asset, velocityModifier, dir, pos)


    @Sched.Tick()
    def batchBullets(self):
        inactiveBullets = []

        for bullet in self.activeBullets:
            if not bullet.flying:
                inactiveBullets.append(bullet)
                continue
            bullet.update(self)

        for inactive in inactiveBullets:
            self.activeBullets.remove(inactive)
            self.idleBullets.append(inactive)