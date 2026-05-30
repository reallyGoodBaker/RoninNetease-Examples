from ..math.vec3 import Vector3, vec, cross, normalize, vabs
from ..level.client import LevelClient, compClient
from ..core.basic import levelId


def drawLine(start, end, color, duration=5):
    # type: (Vector3, Vector3, Vector3, float) -> function
    game = LevelClient.getInstance().game
    drawing = compClient.CreateDrawing(levelId())
    shape = drawing.AddLineShape(
        (start.x, start.y, start.z), # type: ignore
        (end.x, end.y, end.z), # type: ignore
        (color.x, color.y, color.z) # type: ignore
    )
    timer = game.AddTimer(duration, lambda: shape.Remove()) # type: ignore
    def cancel():
        shape.Remove()
        game.CancelTimer(timer)
    return cancel # type: ignore


def drawBox(center, size, forward, color=vec((0, 1, 0)), duration=5):
    # type: (Vector3, Vector3, Vector3, tuple|Vector3, float) -> function
    right = normalize(cross(forward, vec((0, 1, 0))))
    up = normalize(cross(right, forward))
    halfSize = size / 2 # type: ignore

    _forward = forward * halfSize.z
    _up = up * halfSize.y
    _right = right * halfSize.x

    # 8个顶点
    vertices = [
        center + _forward + _up + _right,
        center - _forward + _up + _right,
        center - _forward - _up + _right,
        center + _forward - _up + _right,
        center + _forward + _up - _right,
        center - _forward + _up - _right,
        center - _forward - _up - _right,
        center + _forward - _up - _right
    ]

    # 12条线
    lines = [
        (vertices[0], vertices[1]),
        (vertices[1], vertices[2]),
        (vertices[2], vertices[3]),
        (vertices[3], vertices[0]),
        (vertices[4], vertices[5]),
        (vertices[5], vertices[6]),
        (vertices[6], vertices[7]),
        (vertices[7], vertices[4]),
        (vertices[0], vertices[4]),
        (vertices[1], vertices[5]),
        (vertices[2], vertices[6]),
        (vertices[3], vertices[7])
    ]

    shapes = []

    for line in lines:
        shapes.append(drawLine(line[0], line[1], vec(color), duration))

    def cancel():
        for remove in shapes:
            remove()
    return cancel # type: ignore


def drawBoxFromBound(start, end, forward, color=vec((0, 1, 0)), duration=5):
    # type: (Vector3, Vector3, Vector3, tuple|Vector3, float) -> function
    size = end - start
    center = (start + end) / 2 # type: ignore
    return drawBox(center, size, forward, color, duration) # type: ignore


def drawSphere(center, radius=0.3, color=vec((0, 1, 0)), duration=1):
    # type: (Vector3, float, tuple|Vector3, float) -> function
    game = LevelClient.getInstance().game
    drawing = compClient.CreateDrawing(levelId())
    shape = drawing.AddSphereShape(
        (center.x, center.y, center.z), # type: ignore
        radius,
        (color.x, color.y, color.z) # type: ignore
    )
    timer = game.AddTimer(duration, lambda: shape.Remove()) # type: ignore
    def cancel():
        shape.Remove()
        game.CancelTimer(timer)
    return cancel # type: ignore


def drawRect(start, size, color=vec((0, 1, 0)), duration=5):
    game = LevelClient.getInstance().game
    drawing = compClient.CreateDrawing(levelId())
    shape = drawing.AddBoxShape(
        (start.x, start.y, start.z),
        (size.x, size.y, size.z),
        (color.x, color.y, color.z) # type: ignore
    )
    timer = game.AddTimer(duration, lambda: shape.Remove()) # type: ignore
    def cancel():
        shape.Remove()
        game.CancelTimer(timer)
    return cancel


def drawRectFromBound(start, end, color=vec((0, 1, 0)), duration=5):
    size = vabs(end - start)
    return drawRect(start, size, color, duration)