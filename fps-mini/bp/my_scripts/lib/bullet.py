import time
import math

from ..engine.architect.compact import (
    Asset, remote,
    SubsystemClient, ClientSubsystem,
    LevelClient, addTimer, Sched,
    vec, modulo, Vector3, normalize, tup, mul,
    clientApi, compClient, localPlayerId,
    Curve, getBonePosition,
    QueryVariable,
    epsilon,
)
from ..engine.architect.math.utils import entityAabbDef, pointToLineDist, viewToWorld
from ..engine.architect.math.double import clamp, lerp
from ..engine.architect.core.configurator import modConf
from ..engine.architect.utils.enhance.list import find

x = QueryVariable('x')
y = QueryVariable('y')
z = QueryVariable('z')
rx = QueryVariable('rx')
ry = QueryVariable('ry')
scale = QueryVariable('scale')

class BulletBase(object):

    def create(self, asset, velocityModifier, direction, origin):
        # type: (dict, float, Vector3, Vector3) -> None
        projectile = asset['projectile']
        localId = localPlayerId()
        self.ignoreEntities = Asset(projectile['ignoreEntities']).load()
        self.ignoreBlocks = Asset(projectile['ignoreBlocks']).load()
        self.caliber = projectile['caliber']
        self.payloads = asset['payloads']
        self.penetrate = asset['penetrate']
        self.penetrateBlocks = Asset(self.penetrate['penetrateBlocks']).load()
        self.destroy = asset['destroy']
        self.initialSpeed = projectile['baseSpeed'] * velocityModifier # type: float
        self.gravity = vec((0, projectile['gravity'], 0)) # type: Vector3
        self.drag = projectile['drag'] # type: float
        self.visualOffset = getBonePosition(localId, 'muzzle') - vec(compClient.CreateCamera(localId).GetPosition())
        self.origin = origin
        self.pos = origin
        self.velocity = mul(direction, self.initialSpeed) # type: Vector3
        self.speed = self.initialSpeed

        self.createTime = time.time()
        self.prevTime = self.createTime

        self.flying = True
        self.flyTime = 0
        self.distance = epsilon
        self.displacement = 0
        self.damageRemains = 1.0
        self.step = -1

        # 本 tick 内用于“按命中位置插值速度”的状态
        self.tickDt = 0                 # 本 tick 的 dt, 供子段末端速度预估使用
        self.segmentBeginDist = 0       # 当前插值子段的起点(距本 tick 段首的距离)
        self.segmentStartSpeed = self.initialSpeed  # 子段起点速度
        self.segmentEndSpeed = self.initialSpeed    # 子段末端预估速度

        x, y, z = self.origin
        self.dFrameTime = 0
        self.clientEntity = ClientBulletSystem.getInstance().spawnEntity(
            asset['modelAsset']['bulletEntity'],
            (x, y, z),
            (0, 0)
        )
        modelComp = compClient.CreateModel(self.clientEntity)
        modelComp.SetEntityShadowShow(False)


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
        self.tickDt = dt
        self.flyTime = currentTime - self.createTime
        curVelocity = self.velocity
        self.step += 1
        self.dFrameTime = 0

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


    def removeRenderActor(self):
        ClientBulletSystem.getInstance().destroyEntity(self.clientEntity)
        self.clientEntity = None


    def updateRender(self, dt):
        if not self.clientEntity:
            return

        v = self.velocity
        realPos = self.pos - self.origin + self.visualOffset

        # 速度单位已经是 格/秒，直接 extrapolate，不要再乘 16
        pos = realPos + v * dt
        bulletDist = modulo(pos)
        rot = clientApi.GetRotFromDir(tup(v))
        entity = self.clientEntity
        x.setValue(entity, pos.x)
        y.setValue(entity, pos.y)
        z.setValue(entity, pos.z)
        rx.setValue(entity, rot[0])
        ry.setValue(entity, rot[1])
        scaleFactor = bulletDist * 0.0025 + 1
        scale.setValue(entity, bulletDist < 3 and 0 or scaleFactor)
        self.dFrameTime += dt


    def bulletHitTest(self, clientBullet, pos, v, dt):
        # type: (ClientBulletSystem, Vector3, Vector3, float) -> None
        displacement = v * dt
        dist = modulo(displacement)
        self.displacement = dist
        self.segmentBeginDist = 0
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
            # 每个命中点之前, 用当前速度重算 [segmentBeginDist, D] 子段的插值参数
            self.prepareSubSegment()
            hitDist = modulo(vec(result['hitPos']) - pos)
            if result['type'] == 'Block':
                lastHit = result
                beforeSpeed = self.speed
                if self.handleHitBlock(result, clientBullet):
                    break
                if self.speed != beforeSpeed:
                    # 穿块成功: 速度已被扣除, 以本命中点作为下一子段起点
                    self.segmentBeginDist = hitDist
                continue
            if result['entityId'] == localPlayerId() or result['identifier'] in self.ignoreEntities:
                continue
            lastHit = result
            beforeSpeed = self.speed
            if self.handleHitEntity(result, clientBullet, normalize(v)):
                break
            if self.speed != beforeSpeed:
                # 穿实体成功: 以本命中点作为下一子段起点
                self.segmentBeginDist = hitDist

        clientBullet.updateClientVfx(pos, lastHit and vec(lastHit['hitPos']) or pos + displacement, self)


    def predictEndSpeed(self, velocity, remaining):
        # type: (Vector3, float) -> float
        """沿用 update() 的同一模型(重力每 tick 施加, 阻力按 dt 衰减), 预估剩余段末端速度。
        remaining: 剩余段占本 tick 位移的比例, 1 表示整段。"""
        lastVelocity = velocity + self.gravity * remaining
        lastSpeed = modulo(lastVelocity)
        speedDecay = self.drag * lastSpeed ** 2 * self.tickDt * remaining
        return max(lastSpeed - speedDecay, 0)


    def prepareSubSegment(self):
        # type: () -> None
        """以 segmentBeginDist 为当前子段起点, 用当前速度重算子段起点/末端速度。"""
        self.segmentStartSpeed = self.speed
        dist = self.displacement
        if dist <= epsilon:
            self.segmentEndSpeed = self.speed
            return
        remaining = clamp((dist - self.segmentBeginDist) / dist, 0, 1)
        self.segmentEndSpeed = self.predictEndSpeed(self.velocity, remaining)


    def hitSpeedAt(self, hitPos):
        # type: (tuple) -> float
        """按命中点在当前子段内的位置, 线性插值出命中瞬间的速度。"""
        dist = self.displacement
        if dist <= epsilon:
            return self.speed
        sub = dist - self.segmentBeginDist
        if sub <= epsilon:
            return self.segmentStartSpeed
        hitDist = modulo(vec(hitPos) - self.pos)
        t = clamp((hitDist - self.segmentBeginDist) / sub, 0, 1)
        return lerp(self.segmentStartSpeed, self.segmentEndSpeed, t)


    def handleHitBlock(self, result, clientBullet):
        # type: (dict, ClientBulletSystem) -> bool | None
        blockType = result['identifier']
        if blockType in self.ignoreBlocks:
            return False
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
        x, y, z = getBonePosition(entityId, 'head') or (0, 0, 0)
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


    def calcDamage(self, isHeadShot, kinetic, speed):
        headShotMul = (kinetic['headshotMultiplier'] * int(isHeadShot)) or 1
        baseDamage = kinetic['baseDamage']
        damageMul = Asset(kinetic['damageCurve']).load() # type: Curve
        # 按速度曲线读取伤害倍率
        return baseDamage, damageMul.getValue(speed) * headShotMul


    def handlePenetrateEntity(self, entityId, isHeadShot, hitPos, clientBullet):
        # type: (str, bool, tuple, ClientBulletSystem) -> None
        kinetic = self.getPayload('kinetic')
        if kinetic:
            # 先用撞击瞬间(穿透衰减之前)的速度结算伤害, 再扣除穿透损耗
            clientBullet.damageEntity(entityId, isHeadShot, kinetic, hitPos, self)
        self.velocity *= self.penetrate['velocityRetentionPerPass']
        self.speed = modulo(self.velocity)


    def handleKineticPayload(self, entityId, isHeadShot, hitPos, clientBullet):
        # type: (str, bool, tuple, ClientBulletSystem) -> None
        kinetic =  self.getPayload('kinetic')
        if not kinetic:
            return
        clientBullet.damageEntity(entityId, isHeadShot, kinetic, hitPos, self)



@SubsystemClient
class ClientBulletSystem(ClientSubsystem):

    def onInit(self):
        self.canTick = True
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
        kinetic = bullet.getPayload('kinetic')
        if kinetic:
            _, mul = bullet.calcDamage(False, kinetic, bullet.speed)
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


    def damageEntity(self, target, isHeadShot, kinetic, hitPos, bullet):
        # type: (str, bool, dict, tuple, BulletBase) -> None
        caliber = bullet.caliber
        hitSpeed = bullet.hitSpeedAt(hitPos)
        baseDamage, multiplier = bullet.calcDamage(isHeadShot, kinetic, hitSpeed)
        damage = baseDamage * multiplier
        if self.debug:
            shape = self.drawing.AddSphereShape(hitPos, 1, isHeadShot and (1, 0, 0) or (1, 1, 0))
            addTimer(1, lambda: shape.Remove(), False)
            self.level.textNotify.SetLeftCornerNotify('\ndmg: {}\ncaliber: {}\nspeed: {}\nfly time: {}\n'.format(damage, caliber, hitSpeed, int(bullet.flyTime * 1000)))
        remote.client.call(
            'BulletServerAuthSystem.tryDamageEntity', target, damage, isHeadShot, caliber
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


    def createBulletFromFacing(self, asset, velocityModifier, offset):
        localId = localPlayerId()
        persp = self.level.playerView.GetPerspective()
        pos = vec(persp > 1 and compClient.CreatePos(localId).GetPos() or self.level.camera.GetPosition())
        rx, ry = persp != 2                                                 \
            and clientApi.GetRotFromDir(self.level.camera.GetForward())     \
            or compClient.CreateRot(localId).GetRot()
        ox, oy = offset
        dir = vec(clientApi.GetDirFromRot((rx + ox - 0.5, ry + oy)))
        self.createBullet(asset, velocityModifier, dir, pos)


    def onRender(self, dt):
        for bullet in self.activeBullets:
            bullet.updateRender(dt)


    @Sched.Tick()
    def batchBullets(self):
        inactiveBullets = []

        for bullet in self.activeBullets:
            if not bullet.flying:
                bullet.removeRenderActor()
                inactiveBullets.append(bullet)
                continue
            bullet.update(self)

        for inactive in inactiveBullets:
            self.activeBullets.remove(inactive)
            self.idleBullets.append(inactive)