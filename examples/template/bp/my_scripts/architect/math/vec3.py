from mod.common.utils.mcmath import Vector3
import math

def vec(*init):
    if len(init) == 0:
        return Vector3((0, 0, 0))
    elif type(init[0]) == float:
        return Vector3(init)
    elif type(init[0]) == tuple:
        return Vector3(init[0])
    elif hasattr(init[0], 'x'):
        return Vector3((init[0].x, init[0].y, init[0].z))
    else:
        raise TypeError("Invalid argument type '{}': {}".format(type(init[0]), init))

def add(a, b):
    # type: (Vector3, Vector3) -> Vector3
    return a + b # type: ignore

def sub(a, b):
    # type: (Vector3, Vector3) -> Vector3
    return a - b # type: ignore

def mul(a, b):
    # type: (Vector3, float | int) -> Vector3
    return a * b # type: ignore

def div(a, b):
    # type: (Vector3, float | int) -> Vector3
    return a / b # type: ignore

def dot(a, b):
    # type: (Vector3, Vector3) -> float
    return a * b # type: ignore

def cross(a, b):
    # type: (Vector3, Vector3) -> Vector3
    return Vector3.Cross(a, b) # type: ignore

def modulo(a):
    # type: (Vector3) -> float
    return Vector3.Length(a) # type: ignore

def moduloSqrt(a):
    # type: (Vector3) -> float
    return Vector3.LengthSquared(a) # type: ignore

def normalize(a):
    # type: (Vector3) -> Vector3
    return Vector3.Normalized(a) # type: ignore

def compare(a, b):
    # type: (Vector3, Vector3) -> float
    """
    Greater if a > b
    Less if a < b
    Equal if a == b
    """
    return Vector3.LengthSquared(a) - Vector3.LengthSquared(b) # type: ignore

def clamp(v, min, max):
    # type: (Vector3, float, float) -> Vector3
    lenSqrt = Vector3.LengthSquared(v)
    if lenSqrt > max * max: # type: ignore
        return v * (max / math.sqrt(lenSqrt)) # type: ignore
    elif lenSqrt < min * min: # type: ignore
        return v * (min / math.sqrt(lenSqrt)) # type: ignore
    return v

def lerp(a, b, t):
    # type: (Vector3, Vector3, float) -> Vector3
    return a * (1 - t) + b * t # type: ignore

def nlerp(a, b, t):
    # type: (Vector3, Vector3, float) -> Vector3
    """
    a和b应为单位向量，否则插值不经过起点和终点
    """
    return normalize(lerp(a, b, t))

def tup(a):
    # type: (Vector3) -> tuple[float, float, float]
    return a.ToTuple() # type: ignore

def vabs(a):
    return Vector3(abs(a.x), abs(a.y), abs(a.z))
