# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class BlockAnimateRandomTickEvent(ChainedEvent):
    """客户端 - 以摄像机为中心，随机选取周围的方块触发Tick"""
    blockPos = None  # type: tuple
    blockName = None # type: str
    auxData = None   # type: int


class BlockDestroyByLiquidServerEvent(ChainedEvent):
    """服务端 - 方块被水流破坏的事件"""
    x = None           # type: int
    y = None           # type: int
    z = None           # type: int
    liquidName = None  # type: str
    blockName = None   # type: str
    auxValue = None    # type: int
    dimensionId = None # type: int


class BlockLiquidStateChangeAfterServerEvent(ChainedEvent):
    """服务端 - 方块转为含水或者脱离含水(流体)后触发"""
    blockName = None  # type: str
    auxValue = None   # type: int
    dimension = None  # type: int
    x = None          # type: int
    y = None          # type: int
    z = None          # type: int
    turnLiquid = None # type: bool


class BlockLiquidStateChangeServerEvent(ChainedEvent):
    """服务端 - 方块转为含水或者脱离含水(流体)前触发"""
    blockName = None  # type: str
    auxValue = None   # type: int
    dimension = None  # type: int
    x = None          # type: int
    y = None          # type: int
    z = None          # type: int
    turnLiquid = None # type: bool


class BlockNeighborChangedServerEvent(ChainedEvent):
    """服务端 - 自定义方块周围的方块发生变化时触发"""
    dimensionId = None       # type: int
    posX = None              # type: int
    posY = None              # type: int
    posZ = None              # type: int
    blockName = None         # type: str
    auxValue = None          # type: int
    neighborPosX = None      # type: int
    neighborPosY = None      # type: int
    neighborPosZ = None      # type: int
    fromBlockName = None     # type: str
    fromBlockAuxValue = None # type: int
    toBlockName = None       # type: str
    toAuxValue = None        # type: int


class BlockRandomTickServerEvent(ChainedEvent):
    """服务端 - 自定义方块配置netease:random_tick随机tick时"""
    posX = None         # type: int
    posY = None         # type: int
    posZ = None         # type: int
    blockName = None    # type: str
    fullName = None     # type: str
    auxValue = None     # type: int
    brightness = None   # type: int
    dimensionId = None  # type: int


class BlockRemoveServerEvent(ChainedEvent):
    """服务端 - 监听该事件的方块在销毁时触发"""
    x = None         # type: int
    y = None         # type: int
    z = None         # type: int
    fullName = None  # type: str
    auxValue = None  # type: int
    dimension = None # type: int


class BlockSnowStateChangeAfterServerEvent(ChainedEvent):
    """服务端 - 方块转为含雪或者脱离含雪后触发"""
    dimension = None   # type: int
    x = None           # type: int
    y = None           # type: int
    z = None           # type: int
    turnSnow = None    # type: bool
    setBlockType = None # type: int


class BlockSnowStateChangeServerEvent(ChainedEvent):
    """服务端 - 方块转为含雪或者脱离含雪前触发"""
    dimension = None   # type: int
    x = None           # type: int
    y = None           # type: int
    z = None           # type: int
    turnSnow = None    # type: bool
    setBlockType = None # type: int


class BlockStrengthChangedServerEvent(ChainedEvent):
    """服务端 - 自定义机械元件方块红石信号量发生变化时触发"""
    posX = None           # type: int
    posY = None           # type: int
    posZ = None           # type: int
    blockName = None      # type: str
    auxValue = None       # type: int
    newStrength = None    # type: int
    oldStrength = None    # type: int
    dimensionId = None    # type: int


class ChestBlockTryPairWithServerEvent(ChainedEvent):
    """服务端 - 两个并排的小箱子方块准备组合为一个大箱子方块时"""
    cancel = None       # type: bool
    blockX = None       # type: int
    blockY = None       # type: int
    blockZ = None       # type: int
    otherBlockX = None  # type: int
    otherBlockY = None  # type: int
    otherBlockZ = None  # type: int
    dimensionId = None  # type: int


class ClientBlockUseEvent(ChainedEvent):
    """客户端 - 玩家右键点击新版自定义方块时客户端抛出该事件"""
    playerId = None  # type: str
    blockName = None # type: str
    aux = None       # type: int
    cancel = None    # type: bool
    x = None         # type: int
    y = None         # type: int
    z = None         # type: int
    clickX = None    # type: float
    clickY = None    # type: float
    clickZ = None    # type: float


class CommandBlockContainerOpenEvent(ChainedEvent):
    """服务端 - 玩家点击命令方块，尝试打开命令方块的设置界面"""
    playerId = None # type: str
    isBlock = None  # type: bool
    blockX = None   # type: int
    blockY = None   # type: int
    blockZ = None   # type: int
    victimId = None # type: str
    cancel = None   # type: bool


class CommandBlockUpdateEvent(ChainedEvent):
    """服务端 - 玩家尝试修改命令方块的内置命令时"""
    playerId = None   # type: str
    playerUid = None  # type: int
    command = None    # type: str
    isBlock = None    # type: bool
    blockX = None     # type: int
    blockY = None     # type: int
    blockZ = None     # type: int
    victimId = None   # type: str
    cancel = None     # type: bool


class DestroyBlockEvent(ChainedEvent):
    """服务端 - 当方块已经被玩家破坏时触发该事件"""
    x = None              # type: int
    y = None              # type: int
    z = None              # type: int
    face = None           # type: int
    fullName = None       # type: str
    auxData = None        # type: int
    playerId = None       # type: str
    dimensionId = None    # type: int
    dropEntityIds = None  # type: list[str]


class DirtBlockToGrassBlockServerEvent(ChainedEvent):
    """服务端 - 泥土方块变成草方块时触发"""
    dimension = None # type: int
    x = None         # type: int
    y = None         # type: int
    z = None         # type: int


class EntityPlaceBlockAfterServerEvent(ChainedEvent):
    """服务端 - 当生物成功放置方块后触发"""
    x = None          # type: int
    y = None          # type: int
    z = None          # type: int
    fullName = None   # type: str
    auxData = None    # type: int
    entityId = None   # type: str
    dimensionId = None # type: int
    face = None       # type: int


class FallingBlockBreakServerEvent(ChainedEvent):
    """服务端 - 当下落的方块实体被破坏时触发"""
    fallingBlockId = None # type: str
    fallingBlockX = None  # type: float
    fallingBlockY = None  # type: float
    fallingBlockZ = None  # type: float
    blockName = None      # type: str
    fallTickAmount = None # type: int
    dimensionId = None    # type: int
    cancelDrop = None     # type: bool


class FallingBlockCauseDamageBeforeClientEvent(ChainedEvent):
    """客户端 - 当下落的方块开始计算砸到实体的伤害时触发"""
    fallingBlockId = None  # type: str
    fallingBlockX = None   # type: float
    fallingBlockY = None   # type: float
    fallingBlockZ = None   # type: float
    blockName = None       # type: str
    dimensionId = None     # type: int
    collidingEntitys = None # type: list[str]
    fallTickAmount = None  # type: int
    fallDistance = None    # type: float
    isHarmful = None       # type: bool
    fallDamage = None      # type: int


class FallingBlockCauseDamageBeforeServerEvent(ChainedEvent):
    """服务端 - 当下落的方块开始计算砸到实体的伤害时触发"""
    fallingBlockId = None  # type: str
    fallingBlockX = None   # type: float
    fallingBlockY = None   # type: float
    fallingBlockZ = None   # type: float
    blockName = None       # type: str
    dimensionId = None     # type: int
    collidingEntitys = None # type: list[str]
    fallTickAmount = None  # type: int
    fallDistance = None    # type: float
    isHarmful = None       # type: bool
    fallDamage = None      # type: int


class FallingBlockReturnHeavyBlockServerEvent(ChainedEvent):
    """服务端 - 当下落的方块实体变回普通重力方块时触发"""
    fallingBlockId = None    # type: str
    blockX = None            # type: int
    blockY = None            # type: int
    blockZ = None            # type: int
    heavyBlockName = None    # type: str
    prevHereBlockName = None # type: str
    dimensionId = None       # type: int
    fallTickAmount = None    # type: int


class FarmBlockToDirtBlockServerEvent(ChainedEvent):
    """服务端 - 耕地退化为泥土时触发"""
    dimension = None    # type: int
    x = None            # type: int
    y = None            # type: int
    z = None            # type: int
    setBlockType = None # type: int


class GrassBlockToDirtBlockServerEvent(ChainedEvent):
    """服务端 - 草方块变成泥土方块时触发"""
    dimension = None # type: int
    x = None         # type: int
    y = None         # type: int
    z = None         # type: int


class HeavyBlockStartFallingServerEvent(ChainedEvent):
    """服务端 - 当重力方块变为下落的方块实体后触发"""
    fallingBlockId = None # type: str
    blockX = None         # type: int
    blockY = None         # type: int
    blockZ = None         # type: int
    blockName = None      # type: str
    dimensionId = None    # type: int


class HopperTryPullInServerEvent(ChainedEvent):
    """服务端 - 当漏斗上方连接容器后，容器往漏斗开始输入物品时触发"""
    x = None           # type: int
    y = None           # type: int
    z = None           # type: int
    abovePosX = None   # type: int
    abovePosY = None   # type: int
    abovePosZ = None   # type: int
    dimensionId = None # type: int
    canHopper = None   # type: bool


class HopperTryPullOutServerEvent(ChainedEvent):
    """服务端 - 当漏斗以毗邻的方式连接容器时触发"""
    x = None             # type: int
    y = None             # type: int
    z = None             # type: int
    attachedPosX = None  # type: int
    attachedPosY = None  # type: int
    attachedPosZ = None  # type: int
    dimensionId = None   # type: int
    canHopper = None     # type: bool


class ModBlockEntityLoadedClientEvent(ChainedEvent):
    """客户端 - 客户端自定义方块实体初始化完成时触发"""
    posX = None        # type: int
    posY = None        # type: int
    posZ = None        # type: int
    dimensionId = None # type: int
    blockName = None   # type: str


class ModBlockEntityRemoveClientEvent(ChainedEvent):
    """客户端 - 客户端自定义方块实体卸载时触发"""
    posX = None        # type: int
    posY = None        # type: int
    posZ = None        # type: int
    dimensionId = None # type: int
    blockName = None   # type: str


class ModBlockEntityTickClientEvent(ChainedEvent):
    """客户端 - 客户端自定义方块实体tick事件"""
    posX = None        # type: int
    posY = None        # type: int
    posZ = None        # type: int
    dimensionId = None # type: int
    blockName = None   # type: str


class OnAfterFallOnBlockClientEvent(ChainedEvent):
    """客户端 - 当实体降落到方块后客户端触发"""
    entityId = None  # type: str
    posX = None      # type: float
    posY = None      # type: float
    posZ = None      # type: float
    motionX = None   # type: float
    motionY = None   # type: float
    motionZ = None   # type: float
    blockName = None # type: str
    calculate = None # type: bool


class OnAfterFallOnBlockServerEvent(ChainedEvent):
    """服务端 - 当实体降落到方块后服务端触发"""
    entityId = None  # type: str
    posX = None      # type: float
    posY = None      # type: float
    posZ = None      # type: float
    motionX = None   # type: float
    motionY = None   # type: float
    motionZ = None   # type: float
    blockName = None # type: str
    calculate = None # type: bool


class OnBeforeFallOnBlockServerEvent(ChainedEvent):
    """服务端 - 当实体刚降落到方块上时服务端触发"""
    entityId = None    # type: str
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    blockName = None   # type: str
    fallDistance = None # type: float
    cancel = None      # type: bool


class OnEntityInsideBlockClientEvent(ChainedEvent):
    """客户端 - 当实体碰撞盒所在区域有方块时，客户端持续触发"""
    entityId = None        # type: str
    dimensionId = None     # type: int
    slowdownMultiX = None  # type: float
    slowdownMultiY = None  # type: float
    slowdownMultiZ = None  # type: float
    blockX = None          # type: int
    blockY = None          # type: int
    blockZ = None          # type: int
    blockName = None       # type: str
    cancel = None          # type: bool


class OnEntityInsideBlockServerEvent(ChainedEvent):
    """服务端 - 当实体碰撞盒所在区域有方块时，服务端持续触发"""
    entityId = None        # type: str
    slowdownMultiX = None  # type: float
    slowdownMultiY = None  # type: float
    slowdownMultiZ = None  # type: float
    blockX = None          # type: int
    blockY = None          # type: int
    blockZ = None          # type: int
    blockName = None       # type: str
    cancel = None          # type: bool


class OnModBlockNeteaseEffectCreatedClientEvent(ChainedEvent):
    """客户端 - 自定义方块实体绑定的特效创建成功事件"""
    effectName = None  # type: str
    id = None          # type: int
    effectType = None  # type: int
    blockPos = None    # type: tuple


class OnStandOnBlockClientEvent(ChainedEvent):
    """客户端 - 当实体站立到方块上时客户端持续触发"""
    entityId = None     # type: str
    dimensionId = None  # type: int
    posX = None         # type: float
    posY = None         # type: float
    posZ = None         # type: float
    motionX = None      # type: float
    motionY = None      # type: float
    motionZ = None      # type: float
    blockX = None       # type: int
    blockY = None       # type: int
    blockZ = None       # type: int
    blockName = None    # type: str
    cancel = None       # type: bool


class OnStandOnBlockServerEvent(ChainedEvent):
    """服务端 - 当实体站立到方块上时服务端持续触发"""
    entityId = None     # type: str
    dimensionId = None  # type: int
    posX = None         # type: float
    posY = None         # type: float
    posZ = None         # type: float
    motionX = None      # type: float
    motionY = None      # type: float
    motionZ = None      # type: float
    blockX = None       # type: int
    blockY = None       # type: int
    blockZ = None       # type: int
    blockName = None    # type: str
    cancel = None       # type: bool


class PistonActionServerEvent(ChainedEvent):
    """服务端 - 活塞或者粘性活塞推送/缩回影响附近方块时"""
    cancel = None           # type: bool
    action = None           # type: str
    pistonFacing = None     # type: int
    pistonMoveFacing = None # type: int
    dimensionId = None      # type: int
    pistonX = None          # type: int
    pistonY = None          # type: int
    pistonZ = None          # type: int
    blockList = None        # type: list[list[int]]
    breakBlockList = None   # type: list[list[int]]
    entityList = None       # type: list[str]


class PlayerTryDestroyBlockClientEvent(ChainedEvent):
    """客户端 - 当玩家即将破坏方块时，客户端线程触发该事件"""
    x = None          # type: int
    y = None          # type: int
    z = None          # type: int
    face = None       # type: int
    blockName = None  # type: str
    auxData = None    # type: int
    playerId = None   # type: str
    cancel = None     # type: bool


class ServerBlockEntityTickEvent(ChainedEvent):
    """服务端 - 自定义方块配置了netease:block_entity组件并设tick为true时触发"""
    blockName = None # type: str
    dimension = None # type: int
    posX = None      # type: int
    posY = None      # type: int
    posZ = None      # type: int


class ServerBlockUseEvent(ChainedEvent):
    """服务端 - 玩家右键点击新版自定义方块时服务端抛出该事件"""
    playerId = None    # type: str
    blockName = None   # type: str
    aux = None         # type: int
    cancel = None      # type: bool
    x = None           # type: int
    y = None           # type: int
    z = None           # type: int
    clickX = None      # type: float
    clickY = None      # type: float
    clickZ = None      # type: float
    face = None        # type: int
    itemDict = None    # type: dict
    dimensionId = None # type: int


class ServerEntityTryPlaceBlockEvent(ChainedEvent):
    """服务端 - 当生物试图放置方块时触发该事件"""
    x = None          # type: int
    y = None          # type: int
    z = None          # type: int
    fullName = None   # type: str
    auxData = None    # type: int
    entityId = None   # type: str
    dimensionId = None # type: int
    face = None       # type: int
    cancel = None     # type: bool
    clickX = None     # type: float
    clickY = None     # type: float
    clickZ = None     # type: float


class ServerPlaceBlockEntityEvent(ChainedEvent):
    """服务端 - 手动放置或通过接口创建含自定义方块实体的方块时触发"""
    blockName = None # type: str
    dimension = None # type: int
    posX = None      # type: int
    posY = None      # type: int
    posZ = None      # type: int


class ServerPlayerTryDestroyBlockEvent(ChainedEvent):
    """服务端 - 当玩家即将破坏方块时，服务端线程触发该事件"""
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    face = None            # type: int
    fullName = None        # type: str
    auxData = None         # type: int
    playerId = None        # type: str
    dimensionId = None     # type: int
    cancel = None          # type: bool
    spawnResources = None  # type: bool


class ShearsDestoryBlockBeforeClientEvent(ChainedEvent):
    """客户端 - 玩家手持剪刀破坏方块时，有剪刀特殊效果的方块会在客户端触发"""
    blockX = None        # type: int
    blockY = None        # type: int
    blockZ = None        # type: int
    blockName = None     # type: str
    auxData = None       # type: int
    dropName = None      # type: str
    dropCount = None     # type: int
    playerId = None      # type: str
    dimensionId = None   # type: int
    cancelShears = None  # type: bool


class ShearsDestoryBlockBeforeServerEvent(ChainedEvent):
    """服务端 - 玩家手持剪刀破坏方块时，有剪刀特殊效果的方块会在服务端触发"""
    blockX = None        # type: int
    blockY = None        # type: int
    blockZ = None        # type: int
    blockName = None     # type: str
    auxData = None       # type: int
    dropName = None      # type: str
    dropCount = None     # type: int
    playerId = None      # type: str
    dimensionId = None   # type: int
    cancelShears = None  # type: bool


class StartDestroyBlockClientEvent(ChainedEvent):
    """客户端 - 玩家开始挖方块时触发。创造模式下不触发"""
    pos = None        # type: tuple
    blockName = None  # type: str
    auxValue = None   # type: int
    playerId = None   # type: str
    cancel = None     # type: bool
    face = None       # type: int


class StartDestroyBlockServerEvent(ChainedEvent):
    """服务端 - 玩家开始挖方块时触发。创造模式下不触发"""
    pos = None         # type: tuple
    blockName = None   # type: str
    auxValue = None    # type: int
    playerId = None    # type: str
    dimensionId = None # type: int
    cancel = None      # type: bool
    face = None        # type: int


class StepOffBlockClientEvent(ChainedEvent):
    """客户端 - 实体移动离开一个实心方块时触发"""
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    entityId = None    # type: str
    blockName = None   # type: str
    dimensionId = None # type: int


class StepOffBlockServerEvent(ChainedEvent):
    """服务端 - 实体移动离开一个实心方块时触发"""
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    entityId = None    # type: str
    blockName = None   # type: str
    dimensionId = None # type: int


class StepOnBlockClientEvent(ChainedEvent):
    """客户端 - 实体刚移动至一个新实心方块时触发"""
    cancel = None      # type: bool
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    entityId = None    # type: str
    blockName = None   # type: str
    dimensionId = None # type: int


class StepOnBlockServerEvent(ChainedEvent):
    """服务端 - 实体刚移动至一个新实心方块时触发"""
    cancel = None      # type: bool
    blockX = None      # type: int
    blockY = None      # type: int
    blockZ = None      # type: int
    entityId = None    # type: str
    blockName = None   # type: str
    dimensionId = None # type: int