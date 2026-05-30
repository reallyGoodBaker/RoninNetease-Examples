# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class AddExpEvent(ChainedEvent):
    """服务端 - 当玩家增加经验时触发该事件"""
    id = None     # type: str
    addExp = None # type: int


class AddLevelEvent(ChainedEvent):
    """服务端 - 当玩家升级时触发该事件"""
    id = None       # type: str
    addLevel = None # type: int
    newLevel = None # type: int


class CameraMotionStartClientEvent(ChainedEvent):
    """客户端 - 相机运动器开始事件"""
    motionId = None # type: int


class CameraMotionStopClientEvent(ChainedEvent):
    """客户端 - 相机运动器停止事件"""
    motionId = None # type: int
    remove = None   # type: bool


class ChangeLevelUpCostServerEvent(ChainedEvent):
    """服务端 - 获取玩家下一个等级升级经验时，用于重载玩家的升级经验"""
    level = None           # type: int
    levelUpCostExp = None  # type: int
    changed = None         # type: bool


class DimensionChangeClientEvent(ChainedEvent):
    """客户端 - 玩家维度改变时客户端抛出"""
    playerId = None        # type: str
    fromDimensionId = None # type: int
    toDimensionId = None   # type: int
    fromX = None           # type: float
    fromY = None           # type: float
    fromZ = None           # type: float
    toX = None             # type: float
    toY = None             # type: float
    toZ = None             # type: float


class DimensionChangeFinishClientEvent(ChainedEvent):
    """客户端 - 玩家维度改变完成后客户端抛出"""
    playerId = None        # type: str
    fromDimensionId = None # type: int
    toDimensionId = None   # type: int
    toPos = None           # type: tuple


class DimensionChangeFinishServerEvent(ChainedEvent):
    """服务端 - 玩家维度改变完成后服务端抛出"""
    playerId = None        # type: str
    fromDimensionId = None # type: int
    toDimensionId = None   # type: int
    toPos = None           # type: tuple


class DimensionChangeServerEvent(ChainedEvent):
    """服务端 - 玩家维度改变时服务端抛出"""
    playerId = None        # type: str
    fromDimensionId = None # type: int
    toDimensionId = None   # type: int
    fromX = None           # type: float
    fromY = None           # type: float
    fromZ = None           # type: float
    toX = None             # type: float
    toY = None             # type: float
    toZ = None             # type: float


class ExtinguishFireClientEvent(ChainedEvent):
    """客户端 - 玩家扑灭火焰时触发"""
    pos = None      # type: tuple
    playerId = None # type: str
    cancel = None   # type: bool


class ExtinguishFireServerEvent(ChainedEvent):
    """服务端 - 玩家扑灭火焰时触发"""
    pos = None      # type: tuple
    playerId = None # type: str
    cancel = None   # type: bool


class GameTypeChangedClientEvent(ChainedEvent):
    """客户端 - 个人游戏模式发生变化时客户端触发"""
    playerId = None    # type: str
    oldGameType = None # type: int
    newGameType = None # type: int


class GameTypeChangedServerEvent(ChainedEvent):
    """服务端 - 当默认游戏模式或个人游戏模式发生变化时服务端触发"""
    playerId = None    # type: str
    oldGameType = None # type: int
    newGameType = None # type: int


class MountTamingEvent(ChainedEvent):
    """服务端 - 玩家通过骑乘驯服生物后触发该事件"""
    eid = None # type: str
    pid = None # type: str


class OnLocalPlayerActionClientEvent(ChainedEvent):
    """客户端 - 玩家动作事件，当本地玩家开始/停止某些动作时触发该事件"""
    actionType = None # type: int


class OnLocalPlayerStartJumpClientEvent(ChainedEvent):
    """客户端 - 本地玩家开始跳跃时触发"""
    pass


class OnPlayerActionServerEvent(ChainedEvent):
    """服务端 - 玩家动作事件，当玩家开始/停止某些动作时触发该事件"""
    playerId = None   # type: str
    actionType = None # type: int


class OnPlayerHitBlockClientEvent(ChainedEvent):
    """客户端 - 当玩家碰撞到方块时触发该事件"""
    playerId = None  # type: str
    posX = None      # type: int
    posY = None      # type: int
    posZ = None      # type: int
    blockId = None   # type: str
    auxValue = None  # type: int


class OnPlayerHitBlockServerEvent(ChainedEvent):
    """服务端 - 当玩家碰撞到方块时触发该事件"""
    playerId = None    # type: str
    posX = None        # type: int
    posY = None        # type: int
    posZ = None        # type: int
    blockId = None     # type: str
    auxValue = None    # type: int
    dimensionId = None # type: int


class PerspChangeClientEvent(ChainedEvent):
    """客户端 - 视角切换时会触发的事件"""
    source = None # type: int
    to = None     # type: int


class PlayerAttackEntityServerEvent(ChainedEvent):
    """服务端 - 当玩家攻击时触发该事件"""
    playerId = None     # type: str
    victimId = None     # type: str
    damage = None       # type: float
    isValid = None      # type: int
    cancel = None       # type: bool
    isKnockBack = None  # type: bool
    isCrit = None       # type: bool


class PlayerAttackEntityClientEvent(ChainedEvent):
    """客户端 - 当本地玩家攻击时触发该事件"""
    playerId = None # type: str
    victimId = None # type: str
    damage = None   # type: float
    isCrit = None   # type: bool


class PlayerCheatSpinAttackServerEvent(ChainedEvent):
    """服务端 - 玩家开始/结束快速旋转攻击并且不符合发送快速旋转攻击条件时触发"""
    playerId = None  # type: str
    isStart = None   # type: bool


class PlayerDieEvent(ChainedEvent):
    """服务端 - 当玩家死亡时触发该事件"""
    id = None        # type: str
    attacker = None  # type: str
    customTag = None # type: str
    cause = None     # type: str


class PlayerDoInteractServerEvent(ChainedEvent):
    """服务端 - 玩家与有minecraft:interact组件的生物交互时触发"""
    playerId = None        # type: str
    itemDict = None        # type: dict
    interactEntityId = None # type: str


class PlayerEatFoodServerEvent(ChainedEvent):
    """服务端 - 玩家吃下食物时触发"""
    playerId = None  # type: str
    itemDict = None  # type: dict
    hunger = None    # type: int
    nutrition = None # type: float


class PlayerFeedEntityServerEvent(ChainedEvent):
    """服务端 - 玩家喂养生物时触发"""
    playerId = None  # type: str
    entityId = None  # type: str
    itemDict = None  # type: dict
    cancel = None    # type: bool


class PlayerFishingAfterServerEvent(ChainedEvent):
    """服务端 - 玩家钓鱼成功收杆后触发，在钓鱼掉落物生成后触发"""
    playerId = None         # type: str
    hookEntity = None       # type: str
    itemDict = None         # type: dict
    itemList = None         # type: list[dict]
    itemEntityIdList = None # type: list[str]


class PlayerFishingServerEvent(ChainedEvent):
    """服务端 - 玩家钓鱼成功收杆时触发，在钓鱼掉落物生成前触发"""
    playerId = None   # type: str
    hookEntity = None # type: str
    itemDict = None   # type: dict
    itemList = None   # type: list[dict]
    itemChange = None # type: bool
    cancel = None     # type: bool


class PlayerHungerChangeServerEvent(ChainedEvent):
    """服务端 - 玩家饥饿度变化时触发该事件"""
    playerId = None      # type: str
    hungerBefore = None  # type: float
    hunger = None        # type: float
    cancel = None        # type: bool


class PlayerHurtEvent(ChainedEvent):
    """服务端 - 当玩家受伤害前触发该事件"""
    id = None        # type: str
    attacker = None  # type: str
    customTag = None # type: str
    cause = None     # type: str


class PlayerInteractServerEvent(ChainedEvent):
    """服务端 - 玩家可以与实体交互时"""
    cancel = None    # type: bool
    playerId = None  # type: str
    itemDict = None  # type: dict
    victimId = None  # type: str


class PlayerNamedEntityServerEvent(ChainedEvent):
    """服务端 - 玩家用命名牌重命名实体时触发"""
    playerId = None  # type: str
    entityId = None  # type: str
    preName = None   # type: str
    afterName = None # type: str
    cancel = None    # type: bool


class PlayerPermissionChangeClientEvent(ChainedEvent):
    """客户端 - 玩家权限变更事件"""
    causePlayerId = None  # type: str
    playerId = None       # type: str
    oldPermission = None  # type: dict
    newPermission = None  # type: dict
    changeCause = None    # type: int


class PlayerPermissionChangeServerEvent(ChainedEvent):
    """服务端 - 玩家权限变更事件"""
    causePlayerId = None # type: str
    playerId = None      # type: str
    oldPermission = None # type: dict
    newPermission = None # type: dict
    changeCause = None   # type: int
    cancel = None        # type: bool


class PlayerRespawnEvent(ChainedEvent):
    """服务端 - 玩家复活时触发该事件"""
    id = None # type: str


class PlayerRespawnFinishServerEvent(ChainedEvent):
    """服务端 - 玩家复活完毕时触发"""
    playerId = None # type: str


class PlayerSleepServerEvent(ChainedEvent):
    """服务端 - 玩家使用床睡觉成功"""
    playerId = None # type: str


class PlayerSpinAttackServerEvent(ChainedEvent):
    """服务端 - 玩家开始/结束快速旋转攻击时触发"""
    playerId = None        # type: str
    isInWaterOrRain = None # type: bool
    isRiding = None        # type: bool
    isStart = None         # type: bool


class PlayerStartFishingServerEvent(ChainedEvent):
    """服务端 - 玩家开始钓鱼，生成鱼钩时在服务端触发"""
    playerId = None   # type: str
    hookEntity = None # type: str
    itemDict = None   # type: dict
    cancel = None     # type: bool


class PlayerStopSleepServerEvent(ChainedEvent):
    """服务端 - 玩家停止睡觉"""
    playerId = None # type: str


class PlayerTeleportEvent(ChainedEvent):
    """服务端 - 当玩家传送时触发该事件"""
    id = None # type: str


class PlayerTrySleepServerEvent(ChainedEvent):
    """服务端 - 玩家尝试使用床睡觉"""
    playerId = None # type: str
    cancel = None   # type: bool


class ServerPlayerGetExperienceOrbEvent(ChainedEvent):
    """服务端 - 玩家获取经验球时触发的事件"""
    playerId = None        # type: str
    experienceValue = None # type: int
    cancel = None          # type: bool


class StoreBuySuccServerEvent(ChainedEvent):
    """服务端 - 玩家游戏内购买商品时服务端抛出的事件"""
    playerId = None # type: str


class UpdatePlayerSkinClientEvent(ChainedEvent):
    """客户端 - 玩家加入游戏或通过更衣室局内换肤后同步皮肤信息至客户端后触发"""
    playerId = None # type: str