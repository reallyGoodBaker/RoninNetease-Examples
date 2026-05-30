# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class ActorAcquiredItemClientEvent(ChainedEvent):
    """客户端 - 玩家获得物品时客户端抛出的事件"""
    actor = None           # type: str
    secondaryActor = None  # type: str
    itemDict = None        # type: dict
    acquireMethod = None   # type: int


class ActorAcquiredItemServerEvent(ChainedEvent):
    """服务端 - 玩家获得物品时服务端抛出的事件"""
    actor = None           # type: str
    secondaryActor = None  # type: str
    itemDict = None        # type: dict
    acquireMethod = None   # type: int


class ActorUseItemClientEvent(ChainedEvent):
    """客户端 - 玩家使用物品时客户端抛出的事件"""
    playerId = None  # type: str
    itemDict = None  # type: dict
    useMethod = None # type: int


class ActorUseItemServerEvent(ChainedEvent):
    """服务端 - 玩家使用物品生效之前服务端抛出的事件"""
    playerId = None  # type: str
    itemDict = None  # type: dict
    useMethod = None # type: int


class AnvilCreateResultItemAfterClientEvent(ChainedEvent):
    """客户端 - 玩家点击铁砧合成得到的物品时抛出的事件"""
    playerId = None       # type: str
    itemShowName = None   # type: str
    itemDict = None       # type: dict
    oldItemDict = None    # type: dict
    materialItemDict = None # type: dict


class ClientItemTryUseEvent(ChainedEvent):
    """客户端 - 玩家点击右键尝试使用物品时抛出的事件"""
    playerId = None # type: str
    itemDict = None # type: dict
    cancel = None   # type: bool


class ClientItemUseOnEvent(ChainedEvent):
    """客户端 - 玩家在对方块使用物品时抛出的事件"""
    entityId = None       # type: str
    itemDict = None       # type: dict
    x = None              # type: int
    y = None              # type: int
    z = None              # type: int
    blockName = None      # type: str
    blockAuxValue = None  # type: int
    face = None           # type: int
    clickX = None         # type: float
    clickY = None         # type: float
    clickZ = None         # type: float
    ret = None            # type: bool


class ClientShapedRecipeTriggeredEvent(ChainedEvent):
    """客户端 - 玩家合成物品时触发"""
    recipeId = None # type: str


class ContainerItemChangedServerEvent(ChainedEvent):
    """服务端 - 容器物品变化事件"""
    pos = None          # type: tuple
    containerType = None # type: int
    slot = None         # type: int
    dimensionId = None  # type: int
    oldItemDict = None  # type: dict
    newItemDict = None  # type: dict


class CraftItemOutputChangeServerEvent(ChainedEvent):
    """服务端 - 玩家从容器拿出生成物品时触发"""
    playerId = None            # type: str
    itemDict = None            # type: dict
    screenContainerType = None # type: int
    cancel = None              # type: bool


class CraftUpdateResultItemClientEvent(ChainedEvent):
    """客户端 - 玩家工作台界面更新显示可合成物品时抛出的事件"""
    playerId = None # type: str
    itemDict = None # type: dict


class FurnaceBurnFinishedServerEvent(ChainedEvent):
    """服务端 - 熔炉烧制触发事件"""
    dimensionId = None # type: int
    posX = None        # type: float
    posY = None        # type: float
    posZ = None        # type: float
    itemDict = None    # type: dict


class GrindStoneRemovedEnchantClientEvent(ChainedEvent):
    """客户端 - 玩家点击砂轮合成得到的物品时抛出的事件"""
    playerId = None          # type: str
    oldItemDict = None       # type: dict
    additionalItemDict = None # type: dict
    newItemDict = None       # type: dict
    exp = None               # type: int


class InventoryItemChangedClientEvent(ChainedEvent):
    """客户端 - 玩家背包物品变化时客户端抛出的事件"""
    playerId = None    # type: str
    slot = None        # type: int
    oldItemDict = None # type: dict
    newItemDict = None # type: dict


class InventoryItemChangedServerEvent(ChainedEvent):
    """服务端 - 玩家背包物品变化时服务端抛出的事件"""
    playerId = None    # type: str
    slot = None        # type: int
    oldItemDict = None # type: dict
    newItemDict = None # type: dict


class ItemDurabilityChangedServerEvent(ChainedEvent):
    """服务端 - 物品耐久度变化事件"""
    entityId = None         # type: str
    itemDict = None         # type: dict
    durabilityBefore = None # type: int
    durability = None       # type: int
    canChange = None        # type: bool


class ItemPullOutCustomContainerServerEvent(ChainedEvent):
    """服务端 - 漏出物品到漏斗时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionIndex = None # type: int
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    dimension = None       # type: int
    cancel = None          # type: bool


class ItemPushInCustomContainerServerEvent(ChainedEvent):
    """服务端 - 漏斗漏入物品时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionIndex = None # type: int
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    dimension = None       # type: int
    cancel = None          # type: bool


class ItemReleaseUsingClientEvent(ChainedEvent):
    """客户端 - 释放正在使用的物品"""
    playerId = None       # type: str
    durationLeft = None   # type: float
    itemDict = None       # type: dict
    maxUseDuration = None # type: int
    cancel = None         # type: bool


class ItemReleaseUsingServerEvent(ChainedEvent):
    """服务端 - 释放正在使用的物品时"""
    playerId = None       # type: str
    durationLeft = None   # type: float
    itemDict = None       # type: dict
    maxUseDuration = None # type: int
    cancel = None         # type: bool
    changeItem = None     # type: bool


class ItemUseAfterServerEvent(ChainedEvent):
    """服务端 - 玩家在使用物品之后服务端抛出的事件"""
    entityId = None # type: str
    itemDict = None # type: dict


class ItemUseOnAfterServerEvent(ChainedEvent):
    """服务端 - 玩家在对方块使用物品之后服务端抛出的事件"""
    entityId = None       # type: str
    itemDict = None       # type: dict
    x = None              # type: int
    y = None              # type: int
    z = None              # type: int
    face = None           # type: int
    clickX = None         # type: float
    clickY = None         # type: float
    clickZ = None         # type: float
    blockName = None      # type: str
    blockAuxValue = None  # type: int
    dimensionId = None    # type: int


class LiquidClippedClientEvent(ChainedEvent):
    """客户端 - 玩家客户端点击流体时触发"""
    playerId = None     # type: str
    blockName = None    # type: str
    aux = None          # type: int
    blockPos = None     # type: tuple
    dimensionId = None  # type: int
    floatPos = None     # type: tuple


class LiquidClippedServerEvent(ChainedEvent):
    """服务端 - 玩家服务端点击流体时触发"""
    playerId = None     # type: str
    blockName = None    # type: str
    aux = None          # type: int
    blockPos = None     # type: tuple
    dimensionId = None  # type: int
    floatPos = None     # type: tuple


class OnCarriedNewItemChangedClientEvent(ChainedEvent):
    """客户端 - 手持物品发生变化时触发"""
    itemDict = None # type: dict


class OnCarriedNewItemChangedServerEvent(ChainedEvent):
    """服务端 - 玩家切换主手物品时触发该事件"""
    oldItemDict = None # type: dict
    newItemDict = None # type: dict
    playerId = None    # type: str


class OnItemPutInEnchantingModelServerEvent(ChainedEvent):
    """服务端 - 玩家将可附魔物品放到附魔台上时"""
    playerId = None  # type: str
    slotType = None  # type: int
    options = None   # type: list
    change = None    # type: bool


class OnNewArmorExchangeServerEvent(ChainedEvent):
    """服务端 - 玩家切换盔甲时触发该事件"""
    slot = None        # type: int
    oldArmorDict = None # type: dict
    newArmorDict = None # type: dict
    playerId = None    # type: str


class OnOffhandItemChangedServerEvent(ChainedEvent):
    """服务端 - 玩家切换副手物品时触发该事件"""
    oldItemDict = None # type: dict
    newItemDict = None # type: dict
    playerId = None    # type: str


class OnPlayerActiveShieldServerEvent(ChainedEvent):
    """服务端 - 玩家激活/取消激活盾牌触发的事件"""
    playerId = None   # type: str
    isActive = None   # type: bool
    itemDict = None   # type: dict
    cancelable = None # type: bool
    cancel = None     # type: bool


class OnPlayerBlockedByShieldAfterServerEvent(ChainedEvent):
    """服务端 - 玩家使用盾牌抵挡伤害之后触发"""
    playerId = None  # type: str
    sourceId = None  # type: str
    itemDict = None  # type: dict
    damage = None    # type: float


class OnPlayerBlockedByShieldBeforeServerEvent(ChainedEvent):
    """服务端 - 玩家使用盾牌抵挡伤害之前触发"""
    playerId = None # type: str
    sourceId = None # type: str
    itemDict = None # type: dict
    damage = None   # type: float


class PlayerAddCustomContainerItemClientEvent(ChainedEvent):
    """客户端 - 玩家成功将物品添加到自定义容器时触发该事件"""
    beforeItemDict = None   # type: dict
    changedItemDict = None  # type: dict
    afterItemDict = None    # type: dict
    collectionName = None   # type: str
    collectionType = None   # type: str
    collectionIndex = None  # type: int
    x = None                # type: int
    y = None                # type: int
    z = None                # type: int


class PlayerAddCustomContainerItemServerEvent(ChainedEvent):
    """服务端 - 玩家向自定义容器中添加物品成功后触发该事件"""
    beforeItemDict = None   # type: dict
    changedItemDict = None  # type: dict
    afterItemDict = None    # type: dict
    collectionName = None   # type: str
    collectionType = None   # type: str
    collectionIndex = None  # type: int
    playerId = None         # type: str
    x = None                # type: int
    y = None                # type: int
    z = None                # type: int


class PlayerDropItemServerEvent(ChainedEvent):
    """服务端 - 玩家丢弃物品时触发"""
    playerId = None    # type: str
    itemEntityId = None # type: str


class PlayerPickupArrowServerEvent(ChainedEvent):
    """服务端 - 玩家即将捡起抛射物时触发"""
    playerId = None   # type: str
    arrowId = None    # type: str
    itemDict = None   # type: dict
    cancel = None     # type: bool
    pickupDelay = None # type: int


class PlayerRemoveCustomContainerItemClientEvent(ChainedEvent):
    """客户端 - 玩家成功从自定义容器中移除物品时触发该事件"""
    beforeItemDict = None   # type: dict
    changedItemDict = None  # type: dict
    afterItemDict = None    # type: dict
    collectionName = None   # type: str
    collectionType = None   # type: str
    collectionIndex = None  # type: int
    x = None                # type: int
    y = None                # type: int
    z = None                # type: int


class PlayerRemoveCustomContainerItemServerEvent(ChainedEvent):
    """服务端 - 玩家从自定义容器中移除物品成功后触发该事件"""
    beforeItemDict = None   # type: dict
    changedItemDict = None  # type: dict
    afterItemDict = None    # type: dict
    collectionName = None   # type: str
    collectionType = None   # type: str
    collectionIndex = None  # type: int
    playerId = None         # type: str
    x = None                # type: int
    y = None                # type: int
    z = None                # type: int


class PlayerTryAddCustomContainerItemClientEvent(ChainedEvent):
    """客户端 - 玩家尝试将物品添加到自定义容器时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    cancel = None          # type: bool


class PlayerTryAddCustomContainerItemServerEvent(ChainedEvent):
    """服务端 - 玩家尝试将物品添加到自定义容器时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    playerId = None        # type: str
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int


class PlayerTryDropItemClientEvent(ChainedEvent):
    """客户端 - 玩家丢弃物品时触发"""
    playerId = None # type: str
    itemDict = None # type: dict
    cancel = None   # type: bool


class PlayerTryPutCustomContainerItemClientEvent(ChainedEvent):
    """客户端 - 玩家尝试将物品放入自定义容器时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    cancel = None          # type: bool


class PlayerTryPutCustomContainerItemServerEvent(ChainedEvent):
    """服务端 - 玩家尝试将物品放入自定义容器时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    playerId = None        # type: str
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    cancel = None          # type: bool


class PlayerTryRemoveCustomContainerItemClientEvent(ChainedEvent):
    """客户端 - 玩家尝试从自定义容器中移除物品时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int
    cancel = None          # type: bool


class PlayerTryRemoveCustomContainerItemServerEvent(ChainedEvent):
    """服务端 - 玩家尝试从自定义容器中移除物品时触发该事件"""
    itemDict = None        # type: dict
    collectionName = None  # type: str
    collectionType = None  # type: str
    collectionIndex = None # type: int
    playerId = None        # type: str
    x = None               # type: int
    y = None               # type: int
    z = None               # type: int


class ServerItemTryUseEvent(ChainedEvent):
    """服务端 - 玩家点击右键尝试使用物品时服务端抛出的事件"""
    playerId = None # type: str
    itemDict = None # type: dict
    cancel = None   # type: bool


class ServerItemUseOnEvent(ChainedEvent):
    """服务端 - 玩家在对方块使用物品之前服务端抛出的事件"""
    entityId = None       # type: str
    itemDict = None       # type: dict
    x = None              # type: int
    y = None              # type: int
    z = None              # type: int
    blockName = None      # type: str
    blockAuxValue = None  # type: int
    face = None           # type: int
    dimensionId = None    # type: int
    clickX = None         # type: float
    clickY = None         # type: float
    clickZ = None         # type: float
    ret = None            # type: bool


class ServerPlayerTryTouchEvent(ChainedEvent):
    """服务端 - 玩家即将捡起物品时触发"""
    playerId = None   # type: str
    entityId = None   # type: str
    itemDict = None   # type: dict
    cancel = None     # type: bool
    pickupDelay = None # type: int


class ShearsUseToBlockBeforeServerEvent(ChainedEvent):
    """服务端 - 实体手持剪刀对方块使用时触发该事件"""
    blockX = None        # type: int
    blockY = None        # type: int
    blockZ = None        # type: int
    blockName = None     # type: str
    auxData = None       # type: int
    dropName = None      # type: str
    dropCount = None     # type: int
    entityId = None      # type: str
    dimensionId = None   # type: int
    cancelShears = None  # type: bool


class StartUsingItemClientEvent(ChainedEvent):
    """客户端 - 玩家使用物品时抛出"""
    playerId = None # type: str
    itemDict = None # type: dict


class StopUsingItemClientEvent(ChainedEvent):
    """客户端 - 玩家停止使用物品时抛出"""
    playerId = None # type: str
    itemDict = None # type: dict


class UIContainerItemChangedServerEvent(ChainedEvent):
    """服务端 - 合成容器物品发生变化时触发"""
    playerId = None    # type: str
    slot = None        # type: int
    oldItemDict = None # type: dict
    newItemDict = None # type: dict