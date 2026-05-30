# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class OnCustomGamepadChangedEvent(ChainedEvent):
    """客户端 - 自定义手柄按键绑定发生改变时触发"""
    name = None   # type: str
    oldKey = None # type: str
    newKey = None # type: str


class OnCustomGamepadPressInGame(ChainedEvent):
    """客户端 - 玩家按下自定义手柄按键时触发"""
    name = None       # type: str
    key = None        # type: str
    category = None   # type: str
    isDown = None     # type: str
    magnitude = None  # type: float
    x = None          # type: float
    y = None          # type: float
    screenName = None # type: str


class OnCustomKeyChangedEvent(ChainedEvent):
    """客户端 - 自定义按键绑定发生改变时触发"""
    name = None   # type: str
    oldKey = None # type: str
    newKey = None # type: str


class OnCustomKeyPressInGame(ChainedEvent):
    """客户端 - 玩家按下自定义按键时触发"""
    name = None       # type: str
    key = None        # type: str
    category = None   # type: str
    isDown = None     # type: str
    screenName = None # type: str