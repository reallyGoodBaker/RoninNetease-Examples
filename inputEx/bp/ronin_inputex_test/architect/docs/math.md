# 数学工具 (architect.math)

`architect.math` 提供了 3D 数学运算和实用工具函数，包括向量、矩阵和空间计算。

## 坐标系

- 右手坐标系
- Y 轴向上
- 旋转顺序: Yaw (绕 Y), Pitch (绕 X), Roll (绕 Z)

## 导入方式

```python
from architect.math import vec3, mat4
from architect.math import vec, Vector3, Matrix
```

---

## Vector3 向量

### 创建向量

```python
v1 = vec(1, 2, 3)              # 从分量创建
v2 = vec((1, 2, 3))            # 从元组创建
v3 = Vector3(1, 2, 3)          # 直接构造
```

### 向量运算

```python
v1 + v2                        # 加法
v1 - v2                        # 减法
v1 * 2.0                       # 标量乘法
v1 / 2.0                       # 标量除法
-v1                            # 取负

vec.add(v1, v2)                # 加法函数
vec.div(v1, 2)                 # 除法函数
vec.modulo(v)                  # 长度取整
vec.normalize(v)               # 归一化
vec.tup(v)                     # 转为元组 (x, y, z)
```

### 向量属性

```python
v.x                            # X 分量
v.y                            # Y 分量
v.z                            # Z 分量
v.Length()                     # 长度
v.Normalized()                 # 归一化后的新向量
v.ToTuple()                    # 转换为元组
```

---

## Matrix 矩阵 (mat4)

### 创建矩阵

```python
from architect.math.mat4 import identity, lookAt, perspective, inverse, multiply

mat = identity()               # 单位矩阵
mat = lookAt(eye, target, up)  # 视图矩阵（观察矩阵）
mat = perspective(fov, aspect, near, far)  # 透视投影矩阵
```

### 矩阵运算

```python
mat3 = multiply(mat1, mat2)    # 矩阵乘法
inv = inverse(mat)             # 矩阵求逆
```

### 矩阵变换

```python
from architect.math.mat4 import transformPoint, transform

# 变换点
result = transformPoint(matrix, point)  # point: Vector3

# 构造变换矩阵
transform(
    identity(),           # 基础矩阵
    vec(pos),             # 位置
    vec(rot),             # 旋转 (yaw, pitch, roll)
    vec(scale)            # 缩放
)

# 世界坐标转屏幕坐标
worldToScreen(
    identity(),           # 模型矩阵
    localViewMatrix(),    # 观察矩阵
    localProjectionMatrix(),  # 投影矩阵
    screenSize(),         # 屏幕尺寸
    worldPoint            # 世界坐标点
)
```

---

## 实用函数 (utils)

### 屏幕坐标

```python
from architect.math.utils import screenSize, localViewMatrix, localProjectionMatrix

size = screenSize()                # 获取屏幕尺寸 (width, height)
viewMat = localViewMatrix()        # 获取当前摄像机观察矩阵
projMat = localProjectionMatrix()  # 获取当前摄像机投影矩阵
```

### 世界坐标 <-> 屏幕坐标

```python
from architect.math.utils import worldPosToScreenPos, screenToWorld

# 世界坐标 -> 屏幕坐标（仅客户端可用）
screenPos = worldPosToScreenPos((x, y, z))  # 返回 Vector3

# 屏幕坐标 -> 世界坐标（射线投射）
worldPos = screenToWorld(modelMatrix, screenPoint, filterType)
```

### 碰撞检测

```python
from architect.math.utils import pointInBox, pointInAabb

# 点是否在盒子内（盒子以原点为中心）
pointInBox((x, y, z), (width, height, depth))  # -> bool

# 点是否在 AABB 内
pointInAabb((x, y, z), (minX, minY, minZ), (maxX, maxY, maxZ))  # -> bool
```

### 实体空间查询

```python
from architect.math.utils import (
    boxOverlap3dClient,    # 指定位置旋转的盒子重叠检测
    boxOverlap3dForward,   # 实体前进方向的盒子重叠检测
    boxOverlap3dFacing,    # 实体面朝方向的盒子重叠检测
    forward,               # 实体前进方向向量
    facing,                # 实体面朝方向向量
    entityAabbDef,         # 实体的 AABB 定义
    around,                # 实体周围实体列表
)

# 检测指定位置旋转的盒子的重叠实体
overlapping = boxOverlap3dClient(pos, rot, size, debug=False)

# 检测实体前进方向盒子重叠
overlapping = boxOverlap3dForward(entityId, (width, height, depth))

# 检测实体面朝方向盒子重叠
overlapping = boxOverlap3dFacing(entityId, (width, height, depth))

# 获取实体前进方向向量（XZ 平面）
dir = forward(entityId, dist=1)          # 返回 Vector3

# 获取实体面朝方向向量
dir = facing(entityId)                   # 返回 Vector3

# 获取实体头部 AABB 定义
minPos, maxPos = entityAabbDef(entityId)  # 返回两个元组

# 获取实体周围指定半径内的实体
entities = around(entityId, radius)
```

### 工具常量

```python
from architect.math.utils import defaultFilters

# Molang 默认过滤器（用于 query 等）
defaultFilters = {
    'any_of': [
        {'subject': 'other', 'test': 'is_family', 'value': 'player'},
        {'subject': 'other', 'test': 'is_family', 'value': 'mob'},
    ]
}
```

---

## Vector4 四维向量

`architect.math.vec4` 提供四维向量，用于 3D 变换中的齐次坐标表示（如 `transformPoint` 内部计算），以及局长算法的部分中间结果。

### 创建 Vector4

```python
from architect.math.vec4 import Vector4, vec4, tup4

v1 = vec4(1, 2, 3, 1)              # 从分量创建 (x, y, z, w)
v2 = vec4()                         # 默认为 (0, 0, 0, 1)
v3 = vec4((1, 2, 3, 1))            # 从元组创建
v4 = vec4(vec3_obj)                 # 从 Vector3 转换 (w=1)
v5 = Vector4(1, 2, 3, 1)           # 直接构造
```

### Vector4 运算

```python
v1 + v2                            # 加法
v1 - v2                            # 减法
v1 * 2.0                           # 标量乘法
v1 / 2.0                           # 标量除法

tup4(v)                            # 转为元组 (x, y, z, w)
```

### Vector4 属性

```python
v.x                                # X 分量
v.y                                # Y 分量
v.z                                # Z 分量
v.w                                # W 分量（齐次坐标）
```

### 使用场景

```python
from architect.math.vec4 import tup4
from architect.math.mat4 import transformPoint

# 矩阵变换点，内部使用齐次坐标
modelCenterPos = tup4(transformPoint(worldMatrix, centerPos))
# 返回 (x, y, z, w) 元组
```

---

## 子模块导入

```python
# 直接从子模块导入（不通过 compact）
from architect.math.vec3 import vec, Vector3
from architect.math.vec4 import vec4, Vector4, tup4
from architect.math.mat4 import identity, lookAt, perspective
from architect.math.utils import worldPosToScreenPos
```

---

## 完整 API 对照

| 功能 | 模块 | 说明 |
|------|------|------|
| 向量创建 | `vec3.vec` | 从元组或分量创建 Vector3 |
| 向量运算 | `vec3.add`, `vec3.div`, `vec3.tup` | 加法, 除法, 转元组 |
| 向量属性 | `Vector3.Length`, `.Normalized` | 长度, 归一化 |
| 齐次坐标 | `vec4.vec4`, `vec4.Vector4`, `vec4.tup4` | 四维向量创建/转换 |
| 单位矩阵 | `mat4.identity` | 创建 4x4 单位矩阵 |
| 观察矩阵 | `mat4.lookAt` | 创建摄像机观察矩阵 |
| 投影矩阵 | `mat4.perspective` | 创建透视投影矩阵 |
| 矩阵求逆 | `mat4.inverse` | 矩阵求逆 |
| 矩阵乘法 | `mat4.multiply` | 矩阵乘法 |
| 点变换 | `mat4.transformPoint` | 变换点坐标 |
| 变换矩阵 | `mat4.transform` | 构造位置+旋转+缩放变换矩阵 |
| 屏幕坐标 | `utils.screenSize` | 获取屏幕尺寸 |
| 世界转屏幕 | `utils.worldPosToScreenPos` | 3D -> 2D |
| 屏幕转世界 | `utils.screenToWorld` | 射线投射 |
| 碰撞检测 | `utils.pointInBox`, `utils.pointInAabb` | 点在盒子内检查 |
| 空间查询 | `utils.boxOverlap3dClient` | 指定旋转盒子的重叠检测 |
| 方向向量 | `utils.forward`, `utils.facing` | 实体方向 |
| AABB | `utils.entityAabbDef` | 实体头部 AABB |
| 周围实体 | `utils.around` | 半径内实体列表 |
| 默认过滤器 | `utils.defaultFilters` | Molang 默认 filter |
