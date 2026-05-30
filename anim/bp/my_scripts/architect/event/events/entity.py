# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class ActorHurtServerEvent(ChainedEvent):
    """服务端 - 生物（包括玩家）受伤时触发"""
    entityId = None       # type: str
    cause = None          # type: str
    damage = None         # type: float
    absorbedDamage = None # type: int
    customTag = None      # type: str


class ActuallyHurtServerEvent(ChainedEvent):
    """服务端 - 实体实际受到伤害时触发，相比于DamageEvent，该伤害为经过护甲及buff计算后，实际的扣血量"""
    srcId = None             # type: str
    projectileId = None      # type: str
    entityId = None          # type: str
    damage = None            # type: float
    invulnerableTime = None  # type: int
    lastHurt = None          # type: float
    cause = None             # type: str
    customTag = None         # type: str


class AddEffectServerEvent(ChainedEvent):
    """服务端 - 实体获得状态效果时"""
    entityId = None       # type: str
    effectName = None     # type: str
    effectDuration = None # type: int
    effectAmplifier = None # type: int
    damage = None         # type: float


class ApproachEntityClientEvent(ChainedEvent):
    """客户端 - 玩家靠近生物时触发"""
    playerId = None  # type: str
    entityId = None  # type: str


class ChangeSwimStateServerEvent(ChainedEvent):
    """服务端 - 实体开始或者结束游泳时"""
    entityId = None  # type: str
    formState = None # type: bool
    toState = None   # type: bool


class DamageEvent(ChainedEvent):
    """服务端 - 实体受到伤害时触发"""
    srcId = None         # type: str
    projectileId = None  # type: str
    entityId = None      # type: str
    damage = None        # type: float
    absorption = None    # type: int
    cause = None         # type: str
    knock = None         # type: bool
    ignite = None        # type: bool
    customTag = None     # type: str


class EntityChangeDimensionServerEvent(ChainedEvent):
    """服务端 - 实体维度改变时服务端抛出"""
    entityId = None        # type: str
    fromDimensionId = None # type: int
    toDimensionId = None   # type: int
    fromX = None           # type: float
    fromY = None           # type: float
    fromZ = None           # type: float
    toX = None             # type: float
    toY = None             # type: float
    toZ = None             # type: float


class EntityDefinitionsEventServerEvent(ChainedEvent):
    """服务端 - 生物定义json文件中设置的event触发时同时触发"""
    entityId = None  # type: str
    eventName = None # type: str


class EntityDieLoottableAfterServerEvent(ChainedEvent):
    """服务端 - 生物死亡掉落物品之后"""
    dieEntityId = None       # type: str
    attacker = None          # type: str
    itemList = None          # type: list[dict]
    itemEntityIdList = None  # type: list[str]


class EntityDieLoottableServerEvent(ChainedEvent):
    """服务端 - 生物死亡掉落物品时"""
    dieEntityId = None  # type: str
    attacker = None     # type: str
    itemList = None     # type: list[dict]
    dirty = None        # type: bool


class EntityDroppedItemServerEvent(ChainedEvent):
    """服务端 - 生物扔出物品时触发"""
    entityId = None     # type: str
    itemDict = None     # type: dict
    itemEntityId = None # type: str


class EntityEffectDamageServerEvent(ChainedEvent):
    """服务端 - 生物受到状态伤害/回复事件"""
    entityId = None           # type: str
    damage = None             # type: float
    attributeBuffType = None  # type: int
    duration = None           # type: float
    lifeTimer = None          # type: float
    isInstantaneous = None    # type: bool
    cause = None              # type: str


class EntityLoadScriptEvent(ChainedEvent):
    """服务端 - 数据库加载实体自定义数据时触发，args为长度为2的list，其中第一个元素为实体id"""
    args = None  # type: list


class EntityModelChangedClientEvent(ChainedEvent):
    """客户端 - 实体模型切换时触发"""
    entityId = None  # type: str
    newModel = None  # type: str
    oldModel = None  # type: str


class EntityMotionStartServerEvent(ChainedEvent):
    """服务端 - 实体运动器开始事件"""
    motionId = None  # type: int
    entityId = None  # type: str


class EntityMotionStopServerEvent(ChainedEvent):
    """服务端 - 实体运动器停止事件"""
    motionId = None  # type: int
    entityId = None  # type: str
    remove = None    # type: bool


class EntityPickupItemServerEvent(ChainedEvent):
    """服务端 - 有minecraft:behavior.pickup_items行为的生物拾取物品时触发"""
    entityId = None      # type: str
    itemDict = None      # type: dict
    secondaryActor = None # type: str


class EntityStartRidingEvent(ChainedEvent):
    """服务端 - 当实体骑乘上另一个实体时触发"""
    id = None     # type: str
    rideId = None # type: str


class EntityStopRidingServerEvent(ChainedEvent):
    """服务端 - 当实体停止骑乘时"""
    id = None                     # type: str
    rideId = None                 # type: str
    exitFromRider = None          # type: bool
    entityIsBeingDestroyed = None # type: bool
    switchingRides = None         # type: bool
    cancel = None                 # type: bool


class EntityStopRidingClientEvent(ChainedEvent):
    """客户端 - 当实体停止骑乘时"""
    id = None                     # type: str
    rideId = None                 # type: str
    exitFromRider = None          # type: bool
    entityIsBeingDestroyed = None # type: bool
    switchingRides = None         # type: bool
    cancel = None                 # type: bool


class EntityTickServerEvent(ChainedEvent):
    """服务端 - 实体tick时触发，20帧每秒"""
    entityId = None    # type: str
    identifier = None  # type: str


class HealthChangeBeforeServerEvent(ChainedEvent):
    """服务端 - 生物生命值或最大生命值发生变化之前触发"""
    entityId = None # type: str
    source = None   # type: float
    to = None       # type: float
    byScript = None # type: bool
    cancel = None   # type: bool


class HealthChangeClientEvent(ChainedEvent):
    """客户端 - 生物生命值发生变化时触发"""
    entityId = None # type: str
    source = None   # type: float
    to = None       # type: float


class HealthChangeServerEvent(ChainedEvent):
    """服务端 - 生物生命值发生变化时触发"""
    entityId = None # type: str
    source = None   # type: float
    to = None       # type: float
    byScript = None # type: bool


class LeaveEntityClientEvent(ChainedEvent):
    """客户端 - 玩家远离生物时触发"""
    playerId = None  # type: str
    entityId = None  # type: str


class MobDieEvent(ChainedEvent):
    """服务端 - 实体死亡时触发"""
    id = None        # type: str
    attacker = None  # type: str
    cause = None     # type: str
    customTag = None # type: str


class MobGriefingBlockServerEvent(ChainedEvent):
    """服务端 - 环境生物改变方块时触发"""
    cancel = None      # type: bool
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    entityId = None    # type: str
    blockName = None   # type: str
    dimensionId = None # type: int


class OnFireHurtEvent(ChainedEvent):
    """服务端 - 生物受到火焰伤害时触发"""
    victim = None       # type: str
    src = None          # type: str
    fireTime = None     # type: float
    cancel = None       # type: bool
    cancelIgnite = None # type: bool


class OnGroundClientEvent(ChainedEvent):
    """客户端 - 实体着地事件"""
    id = None  # type: str


class OnGroundServerEvent(ChainedEvent):
    """服务端 - 实体着地事件"""
    id = None  # type: str


class OnKnockBackServerEvent(ChainedEvent):
    """服务端 - 实体被击退时触发"""
    id = None  # type: str


class OnMobHitBlockServerEvent(ChainedEvent):
    """服务端 - 当生物（不包括玩家）碰撞到方块时触发该事件"""
    entityId = None    # type: str
    posX = None        # type: int
    posY = None        # type: int
    posZ = None        # type: int
    blockId = None     # type: str
    auxValue = None    # type: int
    dimensionId = None # type: int


class OnMobHitMobClientEvent(ChainedEvent):
    """客户端 - 当生物间（包含玩家）碰撞时触发该事件"""
    mobId = None          # type: str
    hittedMobList = None  # type: list[str]


class OnMobHitMobServerEvent(ChainedEvent):
    """服务端 - 当生物间（包含玩家）碰撞时触发该事件"""
    mobId = None          # type: str
    hittedMobList = None  # type: list[str]


class ProjectileCritHitEvent(ChainedEvent):
    """服务端 - 当抛射物与头部碰撞时触发"""
    id = None       # type: str
    targetId = None # type: str


class ProjectileDoHitEffectEvent(ChainedEvent):
    """服务端 - 当抛射物碰撞时触发该事件"""
    id = None            # type: str
    hitTargetType = None # type: str
    targetId = None      # type: str
    hitFace = None       # type: int
    x = None             # type: float
    y = None             # type: float
    z = None             # type: float
    blockPosX = None     # type: int
    blockPosY = None     # type: int
    blockPosZ = None     # type: int
    srcId = None         # type: str
    cancel = None        # type: bool


class RefreshEffectServerEvent(ChainedEvent):
    """服务端 - 实体身上状态效果更新时触发"""
    entityId = None       # type: str
    effectName = None     # type: str
    effectDuration = None # type: int
    effectAmplifier = None # type: int
    damage = None         # type: float


class RemoveEffectServerEvent(ChainedEvent):
    """服务端 - 实体身上状态效果被移除时"""
    entityId = None       # type: str
    effectName = None     # type: str
    effectDuration = None # type: int
    effectAmplifier = None # type: int


class SpawnProjectileServerEvent(ChainedEvent):
    """服务端 - 抛射物生成时触发"""
    projectileId = None         # type: str
    projectileIdentifier = None # type: str
    spawnerId = None            # type: str


class StartRidingClientEvent(ChainedEvent):
    """客户端 - 一个实体即将骑乘另外一个实体"""
    actorId = None   # type: str
    victimId = None  # type: str


class StartRidingServerEvent(ChainedEvent):
    """服务端 - 一个实体即将骑乘另外一个实体"""
    cancel = None   # type: bool
    actorId = None  # type: str
    victimId = None # type: str


class WillAddEffectServerEvent(ChainedEvent):
    """服务端 - 实体即将获得状态效果前"""
    entityId = None       # type: str
    effectName = None     # type: str
    effectDuration = None # type: int
    effectAmplifier = None # type: int
    cancel = None         # type: bool
    damage = None         # type: float


class WillTeleportToServerEvent(ChainedEvent):
    """服务端 - 实体即将传送或切换维度"""
    cancel = None           # type: bool
    entityId = None         # type: str
    fromDimensionId = None  # type: int
    toDimensionId = None    # type: int
    fromX = None            # type: int
    fromY = None            # type: int
    fromZ = None            # type: int
    toX = None              # type: int
    toY = None              # type: int
    toZ = None              # type: int
    cause = None            # type: str