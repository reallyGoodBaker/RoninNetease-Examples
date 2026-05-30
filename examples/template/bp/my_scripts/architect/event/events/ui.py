# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class AchievementButtonMovedClientEvent(ChainedEvent):
    """客户端 - 拖动成就入口结束时触发"""
    oldPosition = None # type: tuple
    newPosition = None # type: tuple


class ClientChestCloseEvent(ChainedEvent):
    """客户端 - 关闭箱子界面时触发"""
    pass


class ClientChestOpenEvent(ChainedEvent):
    """客户端 - 打开箱子界面时触发"""
    playerId = None # type: str
    x = None        # type: int
    y = None        # type: int
    z = None        # type: int


class ClientPlayerInventoryCloseEvent(ChainedEvent):
    """客户端 - 关闭物品背包界面时触发"""
    pass


class ClientPlayerInventoryOpenEvent(ChainedEvent):
    """客户端 - 打开物品背包界面时触发"""
    isCreative = None # type: bool
    cancel = None     # type: bool


class CloseNeteaseShopEvent(ChainedEvent):
    """客户端 - 关闭商城界面时触发"""
    pass


class GridComponentSizeChangedClientEvent(ChainedEvent):
    """客户端 - UI grid控件里格子重新排列时触发"""
    path = None # type: str


class HudButtonChangedClientEvent(ChainedEvent):
    """客户端 - 原生HUD按钮位置或大小发生改变时触发"""
    changedList = None # type: tuple


class OnItemSlotButtonClickedEvent(ChainedEvent):
    """客户端 - 点击快捷栏、背包栏、盔甲栏、副手栏的物品槽时触发"""
    slotIndex = None # type: int


class PlayerChatButtonClickClientEvent(ChainedEvent):
    """客户端 - 玩家点击聊天按钮或回车键触发呼出聊天窗口时抛出"""
    pass


class PlayerInventoryOpenScriptServerEvent(ChainedEvent):
    """服务端 - 某个客户端打开物品背包界面时触发"""
    playerId = None   # type: str
    isCreative = None # type: bool


class PopScreenAfterClientEvent(ChainedEvent):
    """客户端 - screen移除触发"""
    screenName = None # type: str
    screenDef = None  # type: str


class PopScreenEvent(ChainedEvent):
    """客户端 - screen移除触发"""
    screenName = None # type: str
    screenDef = None  # type: str


class PushScreenEvent(ChainedEvent):
    """客户端 - screen创建触发"""
    screenName = None # type: str
    screenDef = None  # type: str


class ScreenSizeChangedClientEvent(ChainedEvent):
    """客户端 - 改变屏幕大小时触发"""
    beforeX = None # type: float
    beforeY = None # type: float
    afterX = None  # type: float
    afterY = None  # type: float


class UiInitFinished(ChainedEvent):
    """客户端 - UI初始化框架完成"""
    pass


class UrgeShipEvent(ChainedEvent):
    """服务端 - 玩家点击商城催促发货按钮时触发"""
    playerId = None # type: str