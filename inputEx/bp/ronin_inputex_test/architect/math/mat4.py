from __future__ import division, print_function
from mod.common.utils.mcmath import Matrix, Vector3
from .vec3 import normalize, dot, cross
from .vec4 import vec4, Vector4, tup4
from .double import epsilon
import math

def identity():
    # type: () -> Matrix
    return Matrix.Create([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])  # type: ignore

def lookAt(eye, target, up):
    # type: (Vector3, Vector3, Vector3) -> Matrix
    # 右手系：相机看向 -Z 方向
    zaxis = normalize(eye - target) # type: ignore
    xaxis = normalize(cross(up, zaxis))
    yaxis = cross(zaxis, xaxis)
    return Matrix.Create([
        [xaxis.x, xaxis.y, xaxis.z, -dot(xaxis, eye)], # type: ignore
        [yaxis.x, yaxis.y, yaxis.z, -dot(yaxis, eye)], # type: ignore
        [zaxis.x, zaxis.y, zaxis.z, -dot(zaxis, eye)], # type: ignore
        [0, 0, 0, 1]
    ]) # type: ignore

def perspective(fov_degrees, aspect, near, far):
    # type: (float, float, float, float) -> Matrix
    # 右手系透视投影矩阵，NDC的z范围映射到[-1, 1]
    # 行向量左乘版本：v' = v * M, 其中 v = [x, y, z, 1]
    # 投影后：x' = a*x, y' = b*y, z' = c*z + d, w' = -z
    # 注意：fov_degrees 为角度制（垂直视场角）
    fov_rad = math.radians(fov_degrees)
    tanHalfFov = math.tan(fov_rad / 2)
    a = 1 / (aspect * tanHalfFov)
    b = 1 / tanHalfFov
    c = -(far + near) / (far - near)
    d = -2 * far * near / (far - near)
    return Matrix.Create([
        [a, 0, 0, 0],
        [0, b, 0, 0],
        [0, 0, c, d],
        [0, 0, -1, 0]
    ]) # type: ignore

def multiply(a, b):
    # type: (Matrix, Matrix) -> Matrix
    return Matrix.matrix4_multiply(a, b) # type: ignore

def transpose(m):
    # type: (Matrix) -> Matrix
    return m.Transpose() # type: ignore

def inverse(m):
    # type: (Matrix) -> Matrix
    return m.Inverse() # type: ignore

def translate(v):
    # type: (Vector3) -> Matrix
    x, y, z = v.ToTuple() # type: ignore
    return Matrix.Create([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ]) # type: ignore

def rotateAxis(axis, angle):
    # type: (Vector3, float) -> Matrix
    x, y, z = normalize(axis).ToTuple() # type: ignore
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix.Create([
        [c + (1 - c) * x * x, (1 - c) * x * y - s * z, (1 - c) * x * z + s * y, 0],
        [(1 - c) * x * y + s * z, c + (1 - c) * y * y, (1 - c) * y * z - s * x, 0],
        [(1 - c) * x * z - s * y, (1 - c) * y * z + s * x, c + (1 - c) * z * z, 0],
        [0, 0, 0, 1]
    ]) # type: ignore

def rotateX(angle):
    # type: (float) -> Matrix
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix.Create([
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1]
    ]) # type: ignore

def rotateY(angle):
    # type: (float) -> Matrix
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix.Create([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1]
    ]) # type: ignore

def rotateZ(angle):
    # type: (float) -> Matrix
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix.Create([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]) # type: ignore

def rotateXYZ(roll, yaw, pitch):
    # type: (float, float, float) -> Matrix
    # 先Z、再Y、最后X（矩阵乘法从右到左应用）
    """
    右手系摄像机正方向为 -Z 轴
    """
    return rotateZ(roll) * rotateY(yaw) * rotateX(pitch) # type: ignore

def scale(s):
    # type: (Vector3) -> Matrix
    x, y, z = s.ToTuple() # type: ignore
    return Matrix.Create([
        [x, 0, 0, 0],
        [0, y, 0, 0],
        [0, 0, z, 0],
        [0, 0, 0, 1]
    ]) # type: ignore

def transform(m, t, r, s):
    # type: (Matrix, Vector3, Vector3, Vector3) -> Matrix
    """
    标准模型变换矩阵：先缩放(S)，再旋转(R)，最后平移(T)
    旋转顺序：绕Z轴(r.z)、绕Y轴(r.y)、绕X轴(r.x)（右手系，逆时针为正）
    矩阵乘法顺序：M_final = M_parent * T * R * S
    其中 M_parent 为输入矩阵 m（通常为单位矩阵或父节点变换）
    """
    # 注意：rotateXYZ 函数期望参数顺序为 (roll, yaw, pitch)
    # 其中 roll = r.z（绕Z轴）, yaw = r.y（绕Y轴）, pitch = r.x（绕X轴）
    rx, ry, rz = r.ToTuple() # type: ignore
    return m * translate(t) * rotateXYZ(rz, ry, rx) * scale(s) # type: ignore

def transformPoint(m, point):
    # type: (Matrix, Vector3) -> Vector4
    """
    使用矩阵变换一个点（包含平移影响）
    将点表示为齐次坐标 [x, y, z, 1] 并进行矩阵乘法
    返回变换后的 Vector4

    你可以使用 vec(Vector4) 将w分量舍弃，得到一个 Vector3
    """
    # 手动矩阵-向量乘法
    # 矩阵访问方法：m[row, col]，4x4矩阵，row和col从0到3
    x, y, z = point.ToTuple() # type: ignore

    rx = m[0,0]*x + m[0,1]*y + m[0,2]*z + m[0,3]*1 # type: ignore
    ry = m[1,0]*x + m[1,1]*y + m[1,2]*z + m[1,3]*1 # type: ignore
    rz = m[2,0]*x + m[2,1]*y + m[2,2]*z + m[2,3]*1 # type: ignore
    rw = m[3,0]*x + m[3,1]*y + m[3,2]*z + m[3,3]*1 # type: ignore

    return vec4(rx, ry, rz, rw)

def transformVector(m, vector):
    # type: (Matrix, Vector3) -> Vector3
    """
    使用矩阵变换一个向量（忽略平移影响）
    将向量表示为齐次坐标 [x, y, z, 0] 并进行矩阵乘法
    返回变换后的 Vector3，适用于法线、方向等
    """
    x, y, z = vector.ToTuple() # type: ignore
    # 忽略平移部分（因为w=0）
    rx = m[0,0]*x + m[0,1]*y + m[0,2]*z
    ry = m[1,0]*x + m[1,1]*y + m[1,2]*z
    rz = m[2,0]*x + m[2,1]*y + m[2,2]*z
    return Vector3(rx, ry, rz)

def localToWorld(modelMatrix, localPoint):
    # type: (Matrix, Vector3) -> Vector4
    """
    将模型局部坐标系中的点转换到世界坐标系
    modelMatrix: 模型到世界的变换矩阵（即模型的世界矩阵）
    localPoint: 在模型局部坐标系中的点
    返回世界坐标系中的点
    """
    return transformPoint(modelMatrix, localPoint)

def worldToLocal(modelMatrix, worldPoint):
    # type: (Matrix, Vector3) -> Vector4
    """
    将世界坐标系中的点转换到模型局部坐标系
    modelMatrix: 模型到世界的变换矩阵（即模型的世界矩阵）
    worldPoint: 在世界坐标系中的点
    返回模型局部坐标系中的点（相对于模型的本地坐标）
    """
    invMatrix = inverse(modelMatrix)
    return transformPoint(invMatrix, worldPoint)

def worldToScreen(modelMatrix, viewMatrix, projectionMatrix, viewport, worldPoint):
    # type: (Matrix, Matrix, Matrix, tuple[int, int], Vector3) -> Vector3
    """
    将世界坐标系中的点转换到屏幕坐标系
    modelMatrix: 模型到世界的变换矩阵（即模型的世界矩阵）
    viewMatrix: 世界到视图的变换矩阵（即摄像机矩阵）
    projectionMatrix: 视图到投影的变换矩阵（即投影矩阵）
    viewport: 屏幕视口（即窗口）
    worldPoint: 在世界坐标系中的点
    返回屏幕坐标系中的点（x, y为屏幕坐标，z为深度值）
    """
    # 先将世界坐标转换到裁剪空间
    mvpMatrix = multiply(projectionMatrix, multiply(viewMatrix, modelMatrix))
    x, y, z, w = tup4(transformPoint(mvpMatrix, worldPoint))
    w += epsilon
    x /= w
    y /= w
    z /= w

    # 直接将 NDC 坐标映射到屏幕坐标
    screenPoint = Vector3(
        (x + 1) * 0.5 * viewport[0],
        (1 - (y + 1) * 0.5) * viewport[1],
        z  # 直接使用 z_ndc 作为深度
    )
    return screenPoint