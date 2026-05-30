# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class AchievementCompleteEvent(ChainedEvent):
    """服务端 - 玩家完成自定义成就时触发该事件"""
    playerId = None       # type: str
    rootNodeId = None     # type: str
    achievementId = None  # type: str
    title = None          # type: str
    description = None    # type: str


class AddEntityClientEvent(ChainedEvent):
    """客户端 - 客户端侧创建新实体时触发"""
    id = None             # type: str
    posX = None           # type: float
    posY = None           # type: float
    posZ = None           # type: float
    dimensionId = None    # type: int
    isBaby = None         # type: bool
    engineTypeStr = None  # type: str
    itemName = None       # type: str
    auxValue = None       # type: int


class AddEntityServerEvent(ChainedEvent):
    """服务端 - 服务端侧创建新实体，或实体从存档加载时触发"""
    id = None             # type: str
    posX = None           # type: float
    posY = None           # type: float
    posZ = None           # type: float
    dimensionId = None    # type: int
    isBaby = None         # type: bool
    engineTypeStr = None  # type: str
    itemName = None       # type: str
    auxValue = None       # type: int


class AddPlayerAOIClientEvent(ChainedEvent):
    """客户端 - 玩家加入游戏时视野内存在其他玩家，或者其余玩家进入当前玩家视野时触发的事件"""
    playerId = None  # type: str


class AddPlayerCreatedClientEvent(ChainedEvent):
    """客户端 - 玩家进入当前玩家所在的区块AOI后，玩家皮肤数据异步加载完成后触发的事件"""
    playerId = None  # type: str


class AddServerPlayerEvent(ChainedEvent):
    """服务端 - 玩家加入时触发该事件"""
    id = None             # type: str
    isTransfer = None     # type: bool
    isReconnect = None    # type: bool
    isPeUser = None       # type: bool
    transferParam = None  # type: str
    uid = None            # type: int
    proxyId = None        # type: int


class ChunkAcquireDiscardedClientEvent(ChainedEvent):
    """客户端 - 客户端区块即将被卸载时"""
    dimension = None   # type: int
    chunkPosX = None   # type: int
    chunkPosZ = None   # type: int


class ChunkAcquireDiscardedServerEvent(ChainedEvent):
    """服务端 - 服务端区块即将被卸载时触发"""
    dimension = None      # type: int
    chunkPosX = None      # type: int
    chunkPosZ = None      # type: int
    entities = None       # type: list[str]
    blockEntities = None  # type: list[dict]


class ChunkGeneratedServerEvent(ChainedEvent):
    """服务端 - 区块创建完成时触发"""
    dimension = None       # type: int
    chunkPosX = None       # type: int
    chunkPosZ = None       # type: int
    blockEntityData = None # type: list[dict] | None


class ChunkLoadedClientEvent(ChainedEvent):
    """客户端 - 客户端区块加载完成时"""
    dimension = None  # type: int
    chunkPosX = None  # type: int
    chunkPosZ = None  # type: int


class ChunkLoadedServerEvent(ChainedEvent):
    """服务端 - 服务端区块加载完成时"""
    dimension = None      # type: int
    chunkPosX = None      # type: int
    chunkPosZ = None      # type: int
    blockEntities = None  # type: list[dict]


class ClientLoadAddonsFinishServerEvent(ChainedEvent):
    """服务端 - 客户端mod加载完成时，服务端触发此事件"""
    playerId = None  # type: str


class CommandEvent(ChainedEvent):
    """服务端 - 玩家请求执行指令时触发"""
    entityId = None  # type: str
    command = None   # type: str
    cancel = None    # type: bool


class CustomCommandTriggerServerEvent(ChainedEvent):
    """服务端 - 自定义命令触发事件"""
    command = None        # type: str
    args = None           # type: list[dict]
    variant = None        # type: int
    origin = None         # type: dict
    return_failed = None  # type: bool
    return_msg_key = None # type: str


class DelServerPlayerEvent(ChainedEvent):
    """服务端 - 删除玩家时触发该事件"""
    id = None         # type: str
    isTransfer = None # type: bool
    uid = None        # type: int


class EntityRemoveEvent(ChainedEvent):
    """服务端 - 实体被删除时触发"""
    id = None  # type: str


class ExplosionServerEvent(ChainedEvent):
    """服务端 - 当发生爆炸时触发"""
    blocks = None      # type: list[list]
    victims = None     # type: list[str] | None
    sourceId = None    # type: str | None
    explodePos = None  # type: list
    dimensionId = None # type: int


class GameRenderTickEvent(ChainedEvent):
    """客户端 - 客户端渲染帧开始时触发该事件,一秒触发次数为当前的帧数"""
    pass


class GlobalCommandServerEvent(ChainedEvent):
    """服务端 - 服务端全局命令事件，包括聊天栏发送、SetCommand接口、命令方块（矿车）、行为包动画执行命令"""
    entityId = None  # type: str
    command = None   # type: str
    blockPos = None  # type: tuple
    dimension = None # type: int
    cancel = None    # type: bool


class LoadClientAddonScriptsAfter(ChainedEvent):
    """客户端 - 客户端加载mod完成事件"""
    pass


class LoadServerAddonScriptsAfter(ChainedEvent):
    """服务端 - 服务器加载完mod时触发"""
    pass


class NewOnEntityAreaEvent(ChainedEvent):
    """服务端 - 当有实体进入或离开注册感应区域时触发该事件"""
    name = None              # type: str
    enteredEntities = None   # type: list[str]
    leftEntities = None      # type: list[str]


class OnCommandOutputClientEvent(ChainedEvent):
    """客户端 - 当command命令有成功消息输出时触发"""
    command = None  # type: str
    message = None  # type: str


class OnCommandOutputServerEvent(ChainedEvent):
    """服务端 - Command命令执行成功事件"""
    command = None  # type: str
    message = None  # type: str


class OnContainerFillLoottableServerEvent(ChainedEvent):
    """服务端 - 随机奖励箱第一次打开根据loottable生成物品时"""
    loottable = None  # type: str
    playerId = None   # type: str
    itemList = None   # type: list
    dirty = None      # type: bool


class OnLightningLevelChangeServerEvent(ChainedEvent):
    """服务端 - 打雷强度发生改变"""
    oldLevel = None  # type: float
    newLevel = None  # type: float


class OnLocalLightningLevelChangeServerEvent(ChainedEvent):
    """服务端 - 独立维度天气打雷强度发生改变时触发"""
    oldLevel = None    # type: float
    newLevel = None    # type: float
    dimensionId = None # type: int


class OnLocalPlayerStopLoading(ChainedEvent):
    """客户端 - 玩家进入存档，出生点地形加载完成时触发"""
    playerId = None  # type: str


class OnLocalRainLevelChangeServerEvent(ChainedEvent):
    """服务端 - 独立维度天气下雨强度发生改变时触发"""
    oldLevel = None    # type: float
    newLevel = None    # type: float
    dimensionId = None # type: int


class OnRainLevelChangeServerEvent(ChainedEvent):
    """服务端 - 下雨强度发生改变"""
    oldLevel = None  # type: float
    newLevel = None  # type: float


class OnScriptTickClient(ChainedEvent):
    """客户端 - 客户端tick事件,1秒30次"""
    pass


class OnScriptTickServer(ChainedEvent):
    """服务端 - 服务器tick时触发,1秒有30个tick"""
    pass


class PlaceNeteaseLargeFeatureServerEvent(ChainedEvent):
    """服务端 - 网易版大型结构即将生成时服务端抛出该事件"""
    dimensionId = None        # type: int
    pos = None                # type: tuple
    rot = None                # type: int
    depth = None              # type: int
    centerPool = None         # type: str
    ignoreFitInContext = None # type: bool
    cancel = None             # type: bool


class PlaceNeteaseStructureFeatureEvent(ChainedEvent):
    """服务端 - 首次生成地形时，结构特征即将生成时服务端抛出该事件"""
    structureName = None  # type: str
    x = None              # type: int
    y = None              # type: int
    z = None              # type: int
    biomeType = None      # type: int
    biomeName = None      # type: str
    dimensionId = None    # type: int
    cancel = None         # type: bool


class PlayerIntendLeaveServerEvent(ChainedEvent):
    """服务端 - 即将删除玩家时触发该事件"""
    playerId = None  # type: str


class PlayerJoinMessageEvent(ChainedEvent):
    """服务端 - 准备显示"xxx加入游戏"的玩家登录提示文字时服务端抛出的事件"""
    id = None      # type: str
    name = None    # type: str
    cancel = None  # type: bool
    message = None # type: str


class PlayerLeftMessageServerEvent(ChainedEvent):
    """服务端 - 准备显示"xxx离开游戏"的玩家离开提示文字时服务端抛出的事件"""
    id = None      # type: str
    name = None    # type: str
    cancel = None  # type: bool
    message = None # type: str


class RemoveEntityClientEvent(ChainedEvent):
    """客户端 - 客户端侧实体被移除时触发"""
    id = None  # type: str


class RemovePlayerAOIClientEvent(ChainedEvent):
    """客户端 - 玩家离开当前玩家视野时触发的事件"""
    playerId = None  # type: str


class ServerChatEvent(ChainedEvent):
    """服务端 - 玩家发送聊天信息时触发"""
    username = None            # type: str
    playerId = None            # type: str
    message = None             # type: str
    cancel = None              # type: bool
    bChatById = None           # type: bool
    bForbid = None             # type: bool
    toPlayerIds = None         # type: list[str]
    gameChatPrefix = None      # type: str
    gameChatPrefixColorR = None # type: float
    gameChatPrefixColorG = None # type: float
    gameChatPrefixColorB = None # type: float


class ServerPostBlockPatternEvent(ChainedEvent):
    """服务端 - 用方块组合生成生物，生成生物之后触发该事件"""
    entityId = None          # type: str
    entityGenerated = None   # type: str
    x = None                 # type: int
    y = None                 # type: int
    z = None                 # type: int
    dimensionId = None       # type: int


class ServerPreBlockPatternEvent(ChainedEvent):
    """服务端 - 用方块组合生成生物，在放置最后一个组成方块时触发该事件"""
    enable = None                 # type: bool
    x = None                      # type: int
    y = None                      # type: int
    z = None                      # type: int
    dimensionId = None            # type: int
    entityWillBeGenerated = None  # type: str


class ServerSpawnMobEvent(ChainedEvent):
    """服务端 - 游戏内自动生成生物，以及使用api生成生物时触发"""
    entityId = None        # type: str
    identifier = None      # type: str
    type = None            # type: int
    baby = None            # type: bool
    x = None               # type: float
    y = None               # type: float
    z = None               # type: float
    dimensionId = None     # type: int
    realIdentifier = None  # type: str
    cancel = None          # type: bool


class UnLoadClientAddonScriptsBefore(ChainedEvent):
    """客户端 - 客户端卸载mod之前触发"""
    pass