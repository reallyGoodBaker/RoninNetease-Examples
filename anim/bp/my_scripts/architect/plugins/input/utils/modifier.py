from ..enum import AxisSwizzleOrder
from ....math.common import *


class InputModifier(object):
    def doModify(self, rawValue):
        # type: (tuple[float, float, float]) -> tuple[float, float, float]
        return rawValue


class Negate(InputModifier):
    def doModify(self, rawValue):
        x, y, z = rawValue
        return -x, -y, -z


class Scale(InputModifier):
    def __init__(self, factor=1.0):
        self.factor = factor

    def doModify(self, rawValue):
        x, y, z = rawValue
        return x * self.factor, y * self.factor, z * self.factor


class DeadZone(InputModifier):
    def __init__(self, lowerThreshold=0.2, upperThreshold=0.95):
        self.lower = lowerThreshold
        self.upper = upperThreshold
        self.diff = upperThreshold - lowerThreshold

    def doModify(self, rawValue):
        inputVec = vec(rawValue)
        dir = normalize(inputVec)
        m = modulo(inputVec)
        if m < self.lower:
            return 0.0, 0.0, 0.0
        elif m > self.upper:
            return dir
        else:
            scale = (m - self.lower) / self.diff
            return tup(dir * scale)


class SwizzleAxis(InputModifier):
    def __init__(self, order=AxisSwizzleOrder.XYZ):
        # type: (AxisSwizzleOrder) -> None
        self.order = order

    def doModify(self, rawValue):
        x, y, z = rawValue
        if self.order == AxisSwizzleOrder.XYZ:
            return x, y, z
        elif self.order == AxisSwizzleOrder.YZX:
            return y, z, x
        elif self.order == AxisSwizzleOrder.ZXY:
            return z, x, y
        elif self.order == AxisSwizzleOrder.XZY:
            return x, z, y
        elif self.order == AxisSwizzleOrder.YXZ:
            return y, x, z
        elif self.order == AxisSwizzleOrder.ZYX:
            return z, y, x
        return rawValue