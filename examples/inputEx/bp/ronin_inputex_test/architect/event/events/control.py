# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class ClientJumpButtonPressDownEvent(ChainedEvent):
    """客户端 - 跳跃按钮按下事件"""
    continueJump = None # type: bool


class ClientJumpButtonReleaseEvent(ChainedEvent):
    """客户端 - 跳跃按钮按下释放事件"""
    pass


class GetEntityByCoordEvent(ChainedEvent):
    """客户端 - 玩家点击屏幕时触发"""
    pass


class GetEntityByCoordReleaseClientEvent(ChainedEvent):
    """客户端 - 玩家点击屏幕后松开时触发"""
    pass


class GyroSensorChangedClientEvent(ChainedEvent):
    """客户端 - 陀螺仪传感器姿态发生变化时触发"""
    xDiff = None       # type: float
    yDiff = None       # type: float
    zDiff = None       # type: float
    orientation = None # type: int
    timestamp = None   # type: float


class HoldBeforeClientEvent(ChainedEvent):
    """客户端 - 玩家长按屏幕，即将响应到游戏内时触发"""
    cancel = None # type: bool


class LeftClickBeforeClientEvent(ChainedEvent):
    """客户端 - 玩家按下攻击/摧毁键时触发"""
    cancel = None # type: bool


class LeftClickReleaseClientEvent(ChainedEvent):
    """客户端 - 玩家松开攻击/摧毁键时触发"""
    pass


class MouseWheelClientEvent(ChainedEvent):
    """客户端 - 鼠标滚轮滚动时触发"""
    direction = None # type: int


class OnBackButtonReleaseClientEvent(ChainedEvent):
    """客户端 - 返回按钮松开时触发"""
    pass


class OnClientPlayerStartMove(ChainedEvent):
    """客户端 - 移动按钮按下触发事件"""
    pass


class OnClientPlayerStopMove(ChainedEvent):
    """客户端 - 移动按钮按下释放时触发事件"""
    pass


class OnGamepadControllerLayoutChangeClientEvent(ChainedEvent):
    """客户端 - 游戏手柄按键映射改变事件"""
    action = None # type: str
    newKey = None # type: int
    oldKey = None # type: int


class OnGamepadKeyPressClientEvent(ChainedEvent):
    """客户端 - 游戏手柄按键事件"""
    screenName = None # type: str
    key = None        # type: int
    isDown = None     # type: str


class OnGamepadStickClientEvent(ChainedEvent):
    """客户端 - 游戏手柄摇杆事件"""
    key = None # type: int
    x = None   # type: float
    y = None   # type: float


class OnGamepadTriggerClientEvent(ChainedEvent):
    """客户端 - 游戏手柄扳机事件"""
    key = None       # type: int
    magnitude = None # type: float


class OnKeyPressInGame(ChainedEvent):
    """客户端 - 按键按下或按键释放时触发"""
    screenName = None # type: str
    key = None        # type: str
    isDown = None     # type: str


class OnKeyboardControllerLayoutChangeClientEvent(ChainedEvent):
    """客户端 - 键盘按键映射改变事件"""
    action = None # type: str
    newKey = None # type: int
    oldKey = None # type: int


class OnMouseMiddleDownClientEvent(ChainedEvent):
    """客户端 - 鼠标按下中键时触发"""
    isDown = None         # type: int
    mousePositionX = None # type: float
    mousePositionY = None # type: float


class RightClickBeforeClientEvent(ChainedEvent):
    """客户端 - 玩家按下使用物品/放置方块键时触发"""
    cancel = None # type: bool


class RightClickReleaseClientEvent(ChainedEvent):
    """客户端 - 玩家松开使用物品/放置方块键时触发"""
    pass


class TapBeforeClientEvent(ChainedEvent):
    """客户端 - 玩家点击屏幕并松手，即将响应到游戏内时触发"""
    cancel = None # type: bool


class TapOrHoldReleaseClientEvent(ChainedEvent):
    """客户端 - 玩家点击屏幕后松手时触发"""
    pass