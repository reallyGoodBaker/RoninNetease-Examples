# 常用工具与扩展 (Utils)

`architect` 提供了丰富的辅助模块，涵盖引擎组件封装、绘图工具、动画效果等。

## 引擎组件封装 (architect.level)

通过 `LevelServer` 和 `LevelClient` 类，静态访问预创建好的引擎组件。

### LevelServer（服务端）

```python
from architect.level.server import LevelServer

LevelServer.game               # 游戏组件
LevelServer.chunkSource        # 区块源
LevelServer.achievement        # 成就
LevelServer.biome              # 生物群系
LevelServer.dimension          # 维度
LevelServer.blockInfo          # 方块信息
LevelServer.weather            # 天气
LevelServer.time               # 时间
LevelServer.block              # 方块
LevelServer.blockEntity        # 方块实体
LevelServer.blockEntityData    # 方块实体数据
LevelServer.blockState         # 方块状态
LevelServer.blockUseEventWhiteList  # 方块使用事件白名单
LevelServer.message            # 消息
LevelServer.command            # 命令
LevelServer.chestBlock         # 箱子
LevelServer.explosion          # 爆炸
LevelServer.extraData          # 额外数据
LevelServer.feature            # 特征
LevelServer.itemBanned         # 禁用物品
LevelServer.mobSpawn           # 生物生成
LevelServer.projectile         # 抛射物
LevelServer.portal             # 传送门
LevelServer.recipe             # 配方
LevelServer.redstone           # 红石
```

### LevelClient（客户端）

```python
from architect.level.client import LevelClient

level = LevelClient.getInstance()

level.localPlayer              # 本地玩家
level.achievement              # 成就
level.actorRender              # 实体渲染
level.biome                    # 生物群系
level.block                    # 方块
level.blockGeometry            # 方块几何
level.blockInfo                # 方块信息
level.blockUseEventWhiteList   # 方块使用事件白名单
level.camera                   # 摄像机
level.chunkSource              # 区块源
level.configClient             # 客户端配置
level.customAudio              # 自定义音频
level.dimension                # 维度
level.drawing                  # 绘制
level.fog                      # 雾
level.game                     # 游戏
level.model                    # 模型
level.neteaseShop              # 网易商店
level.operation                # 操作
level.playerView               # 玩家视角
level.postProcess              # 后处理
level.recipe                   # 配方
level.skyRender                # 天空渲染
level.textBoard                # 文本板
level.textNotify               # 文本通知
level.virtualWorld             # 虚拟世界
level.item                     # 物品
level.neteaseWindow            # 网易窗口
```

## 绘图工具 (architect.utils.drawing)

提供游戏内调试用的 3D 线条绘制功能：

```python
from architect.math.vec3 import vec, Vector3
from architect.utils.drawing import drawLine, drawBox

# 绘制一条线（起点，终点，颜色，持续时间）
drawLine(
    vec((0, 0, 0)),
    vec((10, 0, 0)),
    vec((1, 0, 0)),  # 红色
    duration=5       # 5秒后自动消失
)

# 绘制一个方体框（中心，尺寸，前方方向，颜色，持续时间）
drawBox(
    vec((0, 5, 0)),      # 中心位置
    vec((2, 2, 2)),      # 尺寸 (width, height, depth)
    vec((1, 0, 0)),      # 前方方向
    vec((1, 1, 0)),      # 黄色
    duration=5
)
```

## 客户端工具 (architect.utils.client)

```python
from architect.utils.client import isPlayer

# 判断实体是否为玩家
if isPlayer(entityId):
    print('This is a player')
```

客户端子系统 `ClientUtilsSubsys` 自动注册了两个自定义事件监听器：
- `PlayCustomAudio`：播放自定义音效
- `StopCustomAudio`：停止自定义音效

## 动画与效果

### Molang

```python
# 客户端设置 Molang 变量
from architect.utils.molang.client import setMolang, getMolang

setMolang(entityId, 'variable.my_var', 1.0)
value = getMolang(entityId, 'variable.my_var')

# 服务端设置 Molang 变量
from architect.utils.molang.server import setMolang, getMolang
```

## 设备信息 (architect.utils.device)

获取客户端运行环境信息：

```python
from architect.utils.device.client import *

# 获取设备信息
deviceInfo = getDeviceInfo()
```

## 皮肤形象 (architect.utils.persona)

```python
from architect.utils.persona.client import *
from architect.utils.persona.server import *

# 客户端/服务端的皮肤形象信息
```

## 数据持久化 (architect.persistent)

支持将组件数据同步至持久化存储。结合 `@Component(persist=True)` 使用：

```python
from architect.persistent.client import ClientKVDatabase, ClientKVDatabaseGlobal
from architect.persistent.server import ServerKVDatabase

# 服务端持久化数据库
db = ServerKVDatabase.getInstance()
db.setData('player_score', 100)
score = db.getData('player_score')

# 客户端本地持久化数据库
clientDb = ClientKVDatabase.getInstance()
globalDb = ClientKVDatabaseGlobal.getInstance()
```

## 工具集合 (architect.tools)

```python
from architect.tools import *

# 代码生成工具
generate_md_html  # Markdown → HTML 转换
generate_lang     # 语言文件生成
```

## 不安全模块 (architect.core.unreliable)

```python
from architect.core.unreliable import Unreliable

# 提供 try-call 封装，防止单个异常影响整体流程
class MyClass(Unreliable):
    def risky_method(self):
        raise Exception('Error')

obj = MyClass()
obj.tryCall(obj.risky_method)  # 不会抛出异常