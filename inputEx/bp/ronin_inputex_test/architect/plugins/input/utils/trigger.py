from ..enum import TriggerState, TriggerCombineType
from time import time


class InputTrigger(object):
    """Base class for input triggers.
    Determines when an action event is fired based on input state changes.
    """
    combineType = TriggerCombineType.Or
    def updateState(self, inputVal, deltaTime):
        # type: (InputTrigger, object, float) -> TriggerState
        """Check if this trigger condition is met.
        Returns True if the action should fire.
        """
        return TriggerState.Ongoing


class TriggerDown(InputTrigger):
    combineType = TriggerCombineType.Or
    def updateState(self, rawValue, deltaTime):
        if rawValue.size() > 0:
            return TriggerState.Triggered
        return TriggerState.Empty


class TriggerPressed(InputTrigger):
    combineType = TriggerCombineType.Or

    def __init__(self):
        self._wasPressed = False

    def updateState(self, rawValue, deltaTime):
        pressing = rawValue.size() != 0
        if pressing:
            if self._wasPressed:
                return TriggerState.Empty
            else:
                self._wasPressed = True
                return TriggerState.Triggered
        self._wasPressed = False
        return TriggerState.Empty


class TriggerReleased(InputTrigger):
    combineType = TriggerCombineType.Or

    def __init__(self):
        self._wasPressed = False

    def updateState(self, rawValue, deltaTime):
        pressed = rawValue.size()
        triggered = not pressed and self._wasPressed
        self._wasPressed = pressed
        if triggered:
            return TriggerState.Triggered
        if pressed:
            return TriggerState.Ongoing
        return TriggerState.Empty


class TriggerHold(InputTrigger):
    combineType = TriggerCombineType.Or

    def __init__(self, holdThreshold=0.5, startThreshold=0.0):
        self.startThreshold = startThreshold
        self.holdThreshold = holdThreshold
        self._pressStart = None
        self._pressing = False

    def updateState(self, rawValue, deltaTime):
        pressing = rawValue.size() > 0
        pressed = pressing and not self._pressing
        released = not pressing and self._pressing
        self._pressing = pressing

        if pressed:
            self._pressStart = time()
            # 如果startThreshold为 0 ，则直接返回TriggerState.Ongoing
            return TriggerState.Ongoing if self.startThreshold <= 0 else TriggerState.Empty

        if self._pressStart is None:
            return TriggerState.Empty

        if released:
            self._pressStart = None
            return TriggerState.Empty

        pressTime = time() - self._pressStart
        if pressTime < self.holdThreshold:
            return TriggerState.Ongoing
        return TriggerState.Triggered



class TriggerTap(InputTrigger):
    """Fires if the key is pressed and released within a specified time window."""
    combineType = TriggerCombineType.Or

    def __init__(self, tapTime=0.2):
        self.tapTime = tapTime
        self._timer = 0.0
        self._isDown = False

    def updateState(self, rawValue, deltaTime):
        pressed = rawValue.size() > 0
        if pressed and not self._isDown:
            self._timer = 0.0
            self._isDown = True
            return TriggerState.Ongoing
        if self._isDown:
            if pressed:
                self._timer += deltaTime
                return TriggerState.Ongoing
            else:
                self._isDown = False
                if self._timer <= self.tapTime:
                    self._timer = 0.0
                    return TriggerState.Triggered
                self._timer = 0.0
        return TriggerState.Empty
    

class DoubleTap(InputTrigger):
    combineType = TriggerCombineType.And

    def __init__(self, interval=0.3):
        self.pressing = False
        self.interval = interval
        self.lastTap = 0

    def updateState(self, rawValue, deltaTime):
        pressing = rawValue.size() > 0
        # 松开再按下才能判定为一次主动按下
        pressed = pressing and not self.pressing
        self.pressing = pressing

        # pressed 为 false 时，表示持续按住或不按或松开
        if not pressed:
            if not self.lastTap:
                # 从未按下
                return TriggerState.Empty
            else:
                # 按住或松开或不按都必须默认转换到 Ongoing, 因为已经按下过一次了
                # 此时需要再次判断是否超时
                if time() - self.lastTap > self.interval:
                    self.lastTap = 0
                    return TriggerState.Empty
                else:
                    return TriggerState.Ongoing

        # 第一次按下
        if not self.lastTap:
            self.lastTap = time()
            return TriggerState.Ongoing

        # 第二次按下
        self.lastTap = 0
        return TriggerState.Triggered
