# metallic_without_smooth 材质实现笔记

本文记录如何在网易《我的世界》中国版中实现一个自定义实体材质 `metallic_without_smooth`，以及实现过程中踩到的坑、网易版和国际版的区别。

---

## 1. 最终效果

- 中等金属质感：不是纯镜面，也不是塑料。
- 没有暴露参数：所有金属度、高光强度、环境光等数值都硬编码在 shader 里。
- 不平滑法线：每个三角面使用同一个平面法线，保留 lowpoly 硬边棱角。

---

## 2. 涉及文件

```
rp/materials/entity.material
rp/shaders/glsl/metallic_without_smooth.fragment
```

### 2.1 材质定义

```json
"metallic_without_smooth:entity_alphatest": {
    "fragmentShader": "shaders/glsl/metallic_without_smooth.fragment",
    "-defines": [
        "FANCY"
    ],
    "+defines": [
        "RNGL_LOCAL_LIGHT"
    ]
}
```

解释：

- `metallic_without_smooth:entity_alphatest`
  - 表示新增一个材质，名字叫 `metallic_without_smooth`；
  - 继承网易的原版实体材质 `entity_alphatest`；
  - 只覆盖片元着色器，顶点着色器复用父材质。
- `fragmentShader`
  - 指定我们自己的片段着色器。
- `-defines: ["FANCY"]`
  - 去掉 `FANCY`，避免网易默认的“花哨光照”参与计算，改为我们自己控制光照。
- `+defines: ["RNGL_LOCAL_LIGHT"]`
  - 让网易的 `entity_alphatest` 顶点着色器额外输出 `worldSpacePos` / `worldSpaceNormal` 等“相机相对世界空间”数据。
  - 这是后面计算视线方向和平面法线的基础。

---

## 3. 片段着色器思路

### 3.1 采样贴图 + Alpha 裁剪

```glsl
vec4 albedo = texture2D(TEXTURE_0, uv);
if (albedo.a < 0.5) {
    discard;
}
```

和原版 `entity_alphatest` 行为一致：透明部分直接丢弃。

### 3.2 强制平面法线，保持 lowpoly

不使用顶点法线，而是在片元里用屏幕空间导数重建面法线：

```glsl
vec3 V = normalize(-worldSpacePos.xyz); // 相机在原点，所以视线方向是 -worldSpacePos

vec3 dpdx = dFdx(worldSpacePos.xyz);
vec3 dpdy = dFdy(worldSpacePos.xyz);
vec3 N = normalize(cross(dpdx, dpdy));

if (dot(N, V) < 0.0) {
    N = -N;
}
```

为什么这么做：

- 顶点法线会被 GPU 在三角形内部插值，导致棱角处看起来“圆滑”。
- 用 `dFdx/dFdy` 求世界坐标在屏幕上的变化率，再做叉积，得到的是当前三角形面的真实朝向。
- 同一个三角形内所有像素得到的法线一致，所以是 flat shading，lowpoly 质感就回来了。
- `dot(N, V) < 0` 时翻转，保证法线朝向相机，避免某些面变黑。

### 3.2.1 worldSpacePos 是什么坐标系？

`worldSpacePos` 名字里带 “world”，但在网易这个引擎里，它其实是**以相机为原点的坐标**，也就是“相机相对世界坐标 / 视图空间风格坐标”，不是绝对的 Minecraft 方块坐标。

为什么这么做：

- MC 的方块坐标可以非常大，比如 `x = 100000`；
- 如果 shader 直接用绝对世界坐标，float 精度会不够，远处物体会抖动；
- 所以引擎把坐标原点移到相机附近，shader 里计算的都是“相对相机的位置”，既省精度又稳定。

在网易的实体顶点着色器里：

```glsl
worldSpacePos = WORLD * entitySpacePosition;
```

- `entitySpacePosition`：模型/实体空间坐标；
- `WORLD`：模型空间 -> “相机相对世界空间”的变换矩阵；
- `worldSpacePos`：变换后得到的**相对相机**的位置。

因此视线方向不要写成 `VIEW_POS - worldSpacePos`，更稳的写法是：

```glsl
vec3 V = normalize(-worldSpacePos.xyz);
```

因为相机在这个坐标系里就是原点 `(0, 0, 0)`，从片元指向相机就是 `-worldSpacePos`。

常用坐标系总结：

| 坐标系 | 含义 | 常见矩阵/变量 |
| --- | --- | --- |
| 模型/实体空间 | 模型自己的局部坐标 | `entitySpacePosition` |
| 相机相对世界空间 | 以相机为原点，避免大坐标精度问题 | `worldSpacePos` |
| 摄像机/视图空间 | 以相机为原点的坐标 | `WORLDVIEW` |
| 裁剪空间 | 用于最终屏幕映射 | `WORLDVIEWPROJ` |

> 注意：网易引擎里有些变量名叫 `positionWS` / `worldSpacePos`，但实际是相机相对坐标。官方 PBR shader 里也有注释明确写过：
> `positionWS in this engine is VIEW-SPACE (camera-origin) position.`
> 所以不要被名字骗了。

### 3.3 中等金属 Blinn-Phong 光照

```glsl
const float metallic = 0.6;
const float specStrength = 1.2;
const float shininess = 24.0;
const float ambient = 0.55;
const float lightStrength = 1.0;

vec3 L = normalize(SUN_DIR.xyz);
vec3 H = normalize(L + V);
float sunFactor = mix(0.55, 1.0, SUN_DIR.w);

float ndl = clamp(dot(N, L), 0.0, 1.0);
float ndh = clamp(dot(N, H), 0.0, 1.0);

float diffuse = (ambient + lightStrength * ndl) * sunFactor;
float spec = pow(ndh, shininess) * specStrength * sunFactor;

vec3 specColor = mix(vec3(0.04), albedo.rgb, metallic);
vec3 engineLight = clamp(light.rgb, vec3(0.4), vec3(1.3));
vec3 color = albedo.rgb * diffuse * engineLight * (1.0 - metallic * 0.3);
color += specColor * spec * (0.6 + 0.4 * ndl) * engineLight;
color += albedo.rgb * 0.12;
```

金属感来源：

- 金属高光颜色使用 `albedo` 染色，而不是纯白高光；
- 金属度越高，漫反射越低、高光越强；
- `metallic = 0.6` 是“中等金属”的折中值。

### 3.4 让枪跟随环境光亮度

网易原版实体光照在手持物品上可能偏暗，但也不能完全不跟环境光。正确做法是：

- 用 `light.rgb` 做主光照，白天亮、晚上暗；
- 加一个下限 `0.4`，避免晚上完全死黑；
- 上限 `1.3`，防止白天过曝。

```glsl
vec3 engineLight = clamp(light.rgb, vec3(0.4), vec3(1.3));
vec3 color = albedo.rgb * diffuse * engineLight * (1.0 - metallic * 0.3);
color += specColor * spec * (0.6 + 0.4 * ndl) * engineLight;
color += albedo.rgb * 0.12;
```

---

## 4. 实现过程中踩过的坑

### 4.1 枪很暗、没有金属光泽

原因：

- 最初使用了 `normalsColor` / `skyLightPerVertex` 这些 varying。
- 但网易的 `entity_alphatest` 顶点着色器默认并不输出它们，导致法线/光照数据不对。
- 还过度依赖 `light.rgb`，在手持/暗处会变得很黑。

解决：

- 增加 `RNGL_LOCAL_LIGHT`，使用真正可用的 `worldSpacePos`；
- 自己计算 Blinn-Phong 金属高光；
- 用 `light.rgb` 做日/夜环境光主亮度，并给 `0.4` 下限避免死黑。

### 4.2 枪变圆滑了

原因：

- 使用顶点传下来的 `worldSpaceNormal`，即使 render controller 写了 `smooth_normal: false`，实际仍可能被插值。

解决：

- 改用 `dFdx/dFdy` 在片元里重建面法线，强制 flat shading。

### 4.3 `pbr_cloth.fragment` 编译报错

原因：

- 这是网易骨骼模型专用的 `pbr_xxx` 系列材质；
- 它和普通实体模型不兼容；
- 是网易引擎内置 shader 本身缺了一个 uniform 声明。

结论：

- 当前项目不要使用 `pbr_xxx` 系列；
- 我们最终没有在资源包里保留任何 `pbr_xxx` 相关文件。

---

## 5. 网易版和国际版的区别

### 5.1 国际版 Minecraft Bedrock

- 材质文件通常是 `materials/entity.material`，使用原版实体材质族。
- 实体顶点着色器一般输出：
  - `light`
  - `fogColor`
  - `normalsColor`
  - `skyLightPerVertex`
- 自定义材质写法示例：

```json
"my_material:entity_alphatest": {
    "fragmentShader": "shaders/glsl/my_material.fragment"
}
```

- 渲染控制器里通常有：

```json
"smooth_normal": false
```

### 5.2 网易版《我的世界》中国版

- 在 `vanilla_netease` 资源包中有一套自己的材质体系。
- 普通实体材质：
  - `entity_alphatest_netease`
  - `entity_alphatest`
  - `entity_for_skeleton`
- 网易骨骼模型材质：
  - `entity_for_skeleton`
  - `netease_entity_skeleton`
  - `pbr_xxx` 系列（PBR、布料、金属等，仅骨骼模型使用）
- 网易实体顶点着色器默认只输出：
  - `light`
  - `fogColor`
- 如果需要世界空间位置/法线，要开启宏：

```json
"+defines": [
    "RNGL_LOCAL_LIGHT"
]
```

开启后顶点着色器会额外输出：

```glsl
varying vec4 worldSpacePos;
varying vec4 worldSpaceNormal;
```

### 5.3 主要区别总结

| 项目 | 国际版 | 网易版 |
| --- | --- | --- |
| 材质资源包 | `vanilla` | `vanilla_netease` |
| 普通实体材质 | `entity_alphatest` 等 | `entity_alphatest_netease` 等 |
| 骨骼模型材质 | 较少开放 | `entity_for_skeleton`、`pbr_xxx` 等 |
| 世界空间 varying | 部分版本有 | 需要 `RNGL_LOCAL_LIGHT` 开启 |
| 自定义 shader 头文件 | `uniformPerFrameConstants.h` 等 | 还有 `neteaseModelFragmentUtil.h`、`neteaseModelVertexUtil.h` |
| PBR 材质 | 较少用于实体 | 网易有独立 `pbr_xxx` 系列，但只适合骨骼模型 |

---

## 6. 如果想微调效果

所有数值都在 `metallic_without_smooth.fragment` 里，可以直接改：

- `metallic`：金属度，`0.0` 塑料，`1.0` 纯金属。
- `specStrength`：高光强度。
- `shininess`：高光锐利程度，越大越亮越集中。
- `ambient`：环境光亮度，避免暗面死黑。
- `lightStrength`：方向光强度。

改完重新加载 shader 或重启游戏即可。
