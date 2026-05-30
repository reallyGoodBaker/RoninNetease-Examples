class Vector4(object):
    def __init__(self, x, y, z, w=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __add__(self, other):
        x, y, z = other.x, other.y, other.z
        w = other.w if hasattr(other, "w") else 1.0
        return Vector4(self.x + x, self.y + y, self.z + z, self.w + w)

    def __sub__(self, other):
        x, y, z = other.x, other.y, other.z
        w = other.w if hasattr(other, "w") else 1.0
        return Vector4(self.x - x, self.y - y, self.z - z, self.w - w)

    def __mul__(self, other):
        if type(other) == float:
            return Vector4(self.x * other, self.y * other, self.z * other, self.w * other)
        else:
            x, y, z = other.x, other.y, other.z
            w = other.w if hasattr(other, "w") else 1.0
            return Vector4(self.x * x, self.y * y, self.z * z, self.w * w)

    def __truediv__(self, other):
        return Vector4(self.x / other, self.y / other, self.z / other, self.w / other)


def vec4(*args):
    if len(args) == 0:
        return Vector4(0.0, 0.0, 0.0, 1.0)
    elif type(args[0]) == float:
        return Vector4(*args)
    elif type(args[0]) == tuple:
        return Vector4(*args[0])
    elif type(args[0]) == Vector4:
        return args[0]
    elif args[0].__class__.__name__ == "Vector3":
        return Vector4(args[0].x, args[0].y, args[0].z, 1.0)
    else:
        raise TypeError("Cannot convert to Vector4: {}".format(args[0]))
    

def tup4(vec):
    return (vec.x, vec.y, vec.z, vec.w)