# Muzzle Flash 后处理：如何判断“背面”/不该被照亮的面

本文记录 `muzzle_flash.fragment` 里是怎么判断一个面是否朝向枪口、是否应该被火焰照亮的。

---

## 1. 为什么不能直接判断“背面”

后处理阶段只有：

- 场景颜色 `TEXTURE_0`
- 深度 `TEXTURE_2`
- 通过深度重建出来的世界/视野坐标 `worldPos`

没有专门的 normal buffer，也没有几何信息，所以不能直接知道“这个像素的法线朝哪”。

因此我们使用**深度重建法线**：从 `worldPos` 的屏幕空间导数算出当前像素所在面的朝向。

---

## 2. 重建面法线

```glsl
vec3 dpdx = dFdx(worldPos);
vec3 dpdy = dFdy(worldPos);
vec3 N = normalize(cross(dpdx, dpdy));
```

- `dFdx(worldPos)`：worldPos 在屏幕 x 方向的变化；
- `dFdy(worldPos)`：worldPos 在屏幕 y 方向的变化；
- 叉积得到垂直于这个屏幕小面片的向量，也就是**面法线**。

由于叉积方向可能正可能反，我们统一把它翻到朝向相机：

```glsl
if (dot(N, -worldPos) < 0.0) {
    N = -N;
}
```

因为 `worldPos` 是相机相对坐标，相机在原点，`-worldPos` 就是“从当前片元指向相机”的方向。

---

## 3. 判断是否朝向枪口

枪口位置是 `EXTRA_VECTOR1.xyz`。

从当前片元指向枪口：

```glsl
vec3 toMuzzle = normalize(muzzlePos - worldPos);
```

然后计算法线和这个方向的点积：

```glsl
float ndl = clamp(dot(N, toMuzzle), 0.0, 1.0);
```

含义：

- `ndl > 0`：这个面朝向枪口 → 应该被照亮；
- `ndl <= 0`：这个面背向枪口 → 不应该被照亮；
- `ndl` 越大，说明越正对枪口，应该越亮。

这就是“判断背面”的核心。

---

## 4. 实际使用

为了避免 0 附近出现硬边，用 `smoothstep` 做柔和过渡：

```glsl
float lightAmount = smoothstep(0.0, 0.25, ndl);
float baseMul = 0.6 * attenuation * factor * dayNightMul * lightAmount;
```

效果：

- `ndl <= 0`：`lightAmount = 0`，完全不亮；
- `ndl >= 0.25`：`lightAmount = 1`，完全照亮；
- 中间平滑过渡。

---

## 5. 这种方法的局限

这是屏幕空间的近似判断，不是真正的物理遮挡。

它只能判断“这个像素的法线是否朝向枪口”，**不能判断枪口到像素之间有没有被其他东西挡住**。

如果要做真正的火焰阴影/遮挡，需要在 shader 里从枪口向当前像素做深度 ray marching：

```text
从 muzzlePos 出发，沿着方向走到 worldPos，
每一步投影到屏幕并采样深度，
如果中途深度比当前点更近，说明被遮挡，就减少光照。
```

当前实现没有做这一步，所以“被枪身挡住但法线恰好朝向枪口”的面仍可能被照亮。

---

## 6. 总结

| 判断 | 方法 |
| --- | --- |
| 面朝哪 | `dFdx/dFdy` 重建法线 |
| 是否朝向枪口 | `dot(N, muzzlePos - worldPos)` |
| 背向枪口 | `ndl <= 0` |
| 柔和过渡 | `smoothstep(0.0, 0.25, ndl)` |
| 真正遮挡 | 需要深度 ray marching，当前未实现 |
