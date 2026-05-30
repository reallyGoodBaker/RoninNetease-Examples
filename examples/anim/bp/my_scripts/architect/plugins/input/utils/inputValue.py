import math

from ..enum import ValueType


class InputValue(object):
    def __init__(self, defaultValue=(0.0, 0.0, 0.0)):
        self.rawValue = defaultValue # type: tuple[float, float, float]

    @property
    def x(self):
        return self.rawValue[0]
    
    @property
    def y(self):
        return self.rawValue[1]
    
    @property
    def z(self):
        return self.rawValue[2]

    def size(self):
        x, y, z = self.rawValue
        return math.sqrt(x*x + y*y + z*z)

    @staticmethod
    def value(value, type=ValueType.Vector3):
        if type == ValueType.Vector3:
            return value
        elif type == ValueType.Vector2:
            return value[0], value[1]
        elif type == ValueType.Double:
            return value[0]
        else:
            return None