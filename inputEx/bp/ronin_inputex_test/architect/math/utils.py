from .mat4 import multiply, worldToScreen, identity, lookAt, perspective, inverse, Matrix, transformPoint, transform
from .vec3 import vec, Vector3, add, div, tup, normalize, modulo
from .vec4 import tup4
from ..level.client import LevelClient, clientApi
from ..core.basic import compClient, compServer
from ..utils.drawing import drawBox, drawLine, drawSphere

from mod.common.minecraftEnum import RayFilterType

import math


def screenSize():
    level = LevelClient.getInstance()
    return level.game.GetScreenSize()


def localViewMatrix():
    level = LevelClient.getInstance()
    camPos = level.camera.GetPosition()
    camForward = level.camera.GetForward()
    target = (
        camPos[0] + camForward[0],
        camPos[1] + camForward[1],
        camPos[2] + camForward[2],
    )
    return lookAt(
        vec(camPos),
        vec(target),
        vec((0, 1, 0))
    )

def localProjectionMatrix():
    level = LevelClient.getInstance()
    screenWidth, screenHeight = screenSize()
    fov = level.camera.GetFov()
    return perspective(
        fov * 1.1,
        screenWidth / screenHeight,
        0.1,
        100
    )

def worldPosToScreenPos(worldPoint):
    # type: (tuple[float, float, float]) -> Vector3
    return worldToScreen(
        identity(),
        localViewMatrix(),
        localProjectionMatrix(),
        screenSize(), # type: ignore
        vec(worldPoint)
    )

def screenToWorld(modelMatrix, screenPoint, filterType=RayFilterType.OnlyBlocks, debug=False): # type: ignore
    # type: (Matrix, Vector3, RayFilterType, bool) -> Vector3 | None
    """
    只能在客户端使用

    将屏幕坐标系中的点转换到世界坐标系
    modelMatrix: 模型到世界的变换矩阵（即模型的世界矩阵）
    viewMatrix: 世界到视图的变换矩阵（即摄像机矩阵）
    projectionMatrix: 视图到投影的变换矩阵（即投影矩阵）
    viewport: 屏幕视口（即窗口）
    screenPoint: 在屏幕坐标系中的点（x, y为屏幕坐标，z为深度值）
    返回世界坐标系中的点
    """
    # 先将屏幕坐标转换到裁剪空间
    w, h = screenSize()
    # TODO: 这只是一个近似值
    nx = (screenPoint.x / w * 2 - 1) * 1 # type: ignore
    ny = (1 - screenPoint.y / h * 2) * 1 # type: ignore
    rayStartNdc = Vector3(nx, ny, -1)
    rayEndNdc = Vector3(nx, ny, 1)
    # 再将裁剪空间坐标转换到世界坐标
    invMvpMatrix = inverse(multiply(localProjectionMatrix(), multiply(localViewMatrix(), modelMatrix)))
    rayStartHomog = transformPoint(invMvpMatrix, rayStartNdc)
    rayEndHomog = transformPoint(invMvpMatrix, rayEndNdc)

    # 透视除法：齐次坐标除以 w，得到 NDC 空间坐标
    rayStart = Vector3(
        rayStartHomog.x / rayStartHomog.w,
        rayStartHomog.y / rayStartHomog.w,
        rayStartHomog.z / rayStartHomog.w
    )
    rayEnd = Vector3(
        rayEndHomog.x / rayEndHomog.w,
        rayEndHomog.y / rayEndHomog.w,
        rayEndHomog.z / rayEndHomog.w
    )
    ray = rayEnd - rayStart
    if debug: drawLine(rayStart, rayEnd, vec((1, 0, 0)), 1)
    # 计算射线
    result = clientApi.getEntitiesOrBlockFromRay(
        tup(rayStart),
        tup(normalize(ray)), # type: ignore
        int(math.ceil(modulo(ray))), # type: ignore
        False,
        filterType # type: ignore
    )
    if not result:
        return None
    raycasted = vec(result[0]['hitPos'])
    if debug: drawSphere(raycasted)
    return raycasted

defaultFilters = {
    "any_of": [
        {
            "subject" : "other",
            "test" :  "is_family",
            "value" :  "player"
        },
        {
            "subject" : "other",
            "test" :  "is_family",
            "value" :  "mob"
        }
    ]
}


def pointInBox(point, box):
    # type: (tuple[float, float, float], tuple[float, float, float]) -> bool
    # box 参数是盒子的全尺寸 (width, height, depth)
    # 假设盒子以原点为中心，范围从 -size/2 到 size/2
    size = box
    half_x = size[0] / 2
    half_y = size[1] / 2
    half_z = size[2] / 2
    return -half_x <= point[0] <= half_x and -half_y <= point[1] <= half_y and -half_z <= point[2] <= half_z

def pointInAabb(point, min, max):
    # type: (tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]) -> bool
    return min[0] <= point[0] <= max[0] and min[1] <= point[1] <= max[1] and min[2] <= point[2] <= max[2]

def boxOverlap3dClient(pos, rot, size, debug=False):
    # type: (tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], bool) -> list[str]
    """
    :param: rot: (yaw, pitch, roll) 弧度
    """
    radius = math.ceil(math.sqrt(size[0] ** 2 + size[2] ** 2))
    x, y, z = pos
    xozProjStart = (
        x - radius,
        y - radius,
        z - radius
    )
    xozProjEnd = (
        x + radius,
        y + radius,
        z + radius
    )
    level = LevelClient.getInstance()
    firstFind = level.game.GetEntitiesInSquareArea(None, xozProjStart, xozProjEnd) # type: ignore
    _transform = transform(
        identity(),
        vec(pos),
        vec(rot),
        vec((1, 1, 1))
    )

    if debug:
        rotX, rotY = math.degrees(rot[0]), -math.degrees(rot[1])
        drawBox(
            vec(pos),
            vec(size),
            vec(clientApi.GetDirFromRot((rotX, rotY))),
            (1, 1, 0)
        )

    worldMatrix = inverse(_transform)
    result = []
    for entityId in firstFind:
        posComp = compClient.CreatePos(entityId)
        centerPos = div(add(vec(posComp.GetPos()), vec(posComp.GetFootPos())), 2)
        modelCenterPos = tup4(transformPoint(worldMatrix, centerPos))
        if pointInBox(modelCenterPos, size): # type: ignore
            result.append(entityId)

    return result


def boxOverlap3dBouding(start, end, forward, debug=False):
    # type: (tuple[float, float, float], tuple[float, float, float], tuple[float, float, float], bool) -> list[str]
    """
    :param: forward: (x, y, z)
    """
    rotX, rotY = clientApi.GetRotFromDir(tup(normalize(vec(forward))))
    size = (
        end[0] - start[0],
        end[1] - start[1],
        end[2] - start[2]
    )
    center = tup((vec(start) + vec(end)) / 2) # type: ignore
    return boxOverlap3dClient(
        center,
        (rotX, rotY, 0),
        size,
        debug
    )


def boxOverlap3dForward(entityId, size, debug=False):
    # type: (str, tuple[float, float, float], bool) -> list[str]
    """
    :param: size: (width, height, depth)
    """
    pos = compClient.CreatePos(entityId).GetPos()
    dir = forward(entityId)
    rot = clientApi.GetRotFromDir(tup(dir))
    zDist = size[2] / 2
    result = boxOverlap3dClient(
        add(vec(pos), dir * zDist).ToTuple(), # type: ignore
        (math.radians(rot[0]), -math.radians(rot[1]), 0), size, debug
    )
    if entityId in result:
        result.remove(entityId)
    return result


def boxOverlap3dFacing(entityId, size, debug=False):
    # type: (str, tuple[float, float, float], bool) -> list[str]
    """
    :param: size: (width, height, depth)
    """
    pos = compClient.CreatePos(entityId).GetPos()
    rot = compClient.CreateRot(entityId).GetRot()
    dir = clientApi.GetDirFromRot(rot)
    result = boxOverlap3dClient(
        add(vec(pos), vec(dir) * 2).ToTuple(), # type: ignore
        (math.radians(rot[0]), -math.radians(rot[1]), 0), size, debug
    )
    result.remove(entityId)
    return result


def forward(entityId, dist=1):
    x, _, z = clientApi.GetDirFromRot(compClient.CreateRot(entityId).GetRot())
    return vec((x, 0, z)).Normalized() * dist # type: ignore


def facing(entityId):
    dir = clientApi.GetDirFromRot(compClient.CreateRot(entityId).GetRot())
    return vec(dir)


def entityAabbDef(entityId):
    molang = compClient.CreateQueryVariable(entityId)
    molang.EvalMolangExpression("t.aabb = q.bone_aabb('head'); t.min = t.aabb.min; t.max = t.aabb.max;")
    mx = molang.EvalMolangExpression("t.min.x")['value'] / 16
    my = molang.EvalMolangExpression("t.min.y")['value'] / 16
    mz = molang.EvalMolangExpression("t.min.z")['value'] / 16
    px = molang.EvalMolangExpression("t.max.x")['value'] / 16
    py = molang.EvalMolangExpression("t.max.y")['value'] / 16
    pz = molang.EvalMolangExpression("t.max.z")['value'] / 16
    return (mx, my, mz), (px, py, pz)


def around(entityId, radius):
    pos = vec(compServer.CreatePos(entityId).GetPos())
    radiusVec = vec((radius, radius, radius))
    aroundEntities = LevelClient.getInstance().game.GetEntitiesInSquareArea(
        None, tup(pos - radiusVec), tup(pos + radiusVec) # type: ignore
    )
    if entityId in aroundEntities:
        aroundEntities.remove(entityId)
    return aroundEntities