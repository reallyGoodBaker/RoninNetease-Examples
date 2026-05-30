# 快速开始

本指南演示如何使用 `architect` 框架构建一个网易《我的世界》模组。

所有 API 均可从 `architect.compact` 按需导入。

---

## 1. 项目结构

```
my_mod/
├── modMain.py              # 模组入口
├── conf.py                 # 配置文件
├── server_system.py        # 服务端子系统
├── client_main.py          # 客户端子系统
├── components.py           # 组件定义
└── architect/              # 框架本体（符号链接或拷贝）
```

---

## 2. 配置文件 `conf.py`

创建 `conf.py`，定义模组引擎名称和系统名称：

```python
# ========== conf.py ==========

MOD_ENGINE_NAME = 'my_mod'      # 引擎命名空间
MOD_SYSTEM_NAME = 'my_system'   # 系统名称
```

---

## 3. 模组入口 `modMain.py`

```python
# ========== modMain.py ==========

from architect.compact import createServer, createClient

def modInit():
    # 读取 conf.py 中的 MOD_ENGINE_NAME 和 MOD_SYSTEM_NAME 完成初始化
    createServer()
    createClient()
```

---

## 4. 服务端子系统

使用 `@SubsystemServer` 装饰器注册子系统和 `Sched.Tick` 装饰器注册定时任务。

```python
# ========== server_system.py ==========

from architect.compact import SubsystemServer
from architect.compact import ServerSubsystem
from architect.compact import Sched, LevelServer

@SubsystemServer
class MyServerSystem(ServerSubsystem):

    def onInit(self):
        print('[Server] Initialized')

    # Sched.Tick() 让此方法在每个 Update 阶段执行
    @Sched.Tick()
    def onTick(self, args):
        print('[Server] Tick')

    def onDestroy(self):
        print('[Server] Destroyed')
```

### Sched 调度装饰器

```python
from architect.compact import Sched, SchedUpdateFlags, SchedEventFlags

# 每帧 Update 阶段执行
@Sched.Tick()

# 在 Update 之前执行
@Sched.Tick(SchedUpdateFlags.BeforeUpdate)

# 在 Update 之后执行
@Sched.Tick(SchedUpdateFlags.AfterUpdate)

# 客户端渲染帧执行
@Sched.Render()

# 固定频率调度器（需配合 scheduleFixed 使用）
@Sched.Fixed('my_fixed_sched')

# 绑定到引擎事件（事件到达时执行）
@Sched.Event('OnEntityDie')
@Sched.Event('OnPlayerAttack', isCustom=False)
```

---

## 5. 客户端子系统

```python
# ========== client_main.py ==========

from architect.compact import SubsystemClient
from architect.compact import ClientSubsystem, LevelClient

@SubsystemClient
class MyClientSystem(ClientSubsystem):

    def onInit(self):
        self.canTick = True
        print('[Client] Initialized')

    # 使用 Sched.Render 实现每帧渲染更新
    @Sched.Render()
    def onRenderTick(self, args):
        pass

    def onDestroy(self):
        print('[Client] Destroyed')
```

---

## 6. 组件 (Component)

### 6.1 定义组件

```python
# ========== components.py ==========

from architect.compact import Component, BaseCompServer, BaseCompClient

# Component() 必须作为函数调用，返回装饰器
@Component()
class HealthCompServer(BaseCompServer):
    def __init__(self):
        self.health = 100
        self.maxHealth = 100

    def onCreate(self, entityId):
        print('HealthComp created for %s' % entityId)

    def takeDamage(self, amount):
        self.health = max(0, self.health - amount)

@Component()
class HealthCompClient(BaseCompClient):
    def __init__(self):
        self.displayHealth = 100

    def onSetData(self, data):
        self.displayHealth = data.get('health', 100)
```

### 6.2 使用组件

```python
from architect.compact import createComponent, getComponent, getEntities, hasComponent

def demo(entityId):
    # 创建组件
    createComponent(entityId, HealthCompServer)

    # 获取组件
    comp = getComponent(entityId, [HealthCompServer])
    if comp:
        healthComp = comp[0]
        healthComp.takeDamage(10)

    # 判断是否拥有组件
    if hasComponent(entityId, HealthCompServer):
        print('Has health component')

    # 获取所有"被标记过"（拥有组件）的实体
    for eid in getEntities():
        print('Entity %s has at least one component' % eid)
```

### 6.3 单例组件

```python
from architect.compact import Component, BaseCompServer

@Component(singleton=True)
class GameConfigComp(BaseCompServer):
    def __init__(self):
        self.maxPlayers = 20
```

### 6.4 使用原生组件常量 (NeC / NeS)

`NeC` 和 `NeS` 只提供原生组件的名称常量，用于 `getComponent` 查询：

```python
from architect.compact import NeC, NeS
from .component.core import getComponent

entityId = 'some_entity'

# 获取原生位置组件（客户端）
posComp = getComponent(entityId, [NeC.Pos])

# 获取原生位置组件（服务端）
posCompSrv = getComponent(entityId, [NeS.Pos])

# 获取健康值组件
healthComp = getComponent(entityId, [NeS.Health])
```

---

## 7. 事件监听

### 7.1 使用 @EventListener 装饰器

```python
from architect.compact import SubsystemServer
from architect.compact import ServerSubsystem
from architect.compact import EventListener, CustomEvent

@SubsystemServer
class EventSystem(ServerSubsystem):

    # @EventListener 装饰器会自动注册监听
    @EventListener('OnEntityDie')
    def onEntityDie(self, ev):
        # ev 是 ChainedEvent 实例，通过属性访问数据
        entityId = ev.id
        print('Entity %s died' % entityId)

    # @CustomEvent 用于监听自定义事件
    @CustomEvent('MyCustomEvent')
    def onCustomEvent(self, ev):
        # ev 是 ChainedEvent 实例
        print('Custom event received: %s' % ev.eventType)
```

### 7.2 ChainedEvent 链式事件

`ChainedEvent` 是事件类，在 `EventChain.dispatch()` 内部自动创建。事件方法感知到的是 `ChainedEvent` 实例：

```python
from architect.compact import ChainedEvent

def eventHandler(ev):
    # ev 是 ChainedEvent 实例
    print(ev.eventType)     # 事件类型
    print(ev.dict())        # 事件数据字典
    ev.stop()               # 停止事件传递
    ev.prevent()            # 阻止默认行为
    ev.setEvent('key', 'value')  # 修改事件数据
```

---

## 8. 实体查询 (@Query + Sched)

`@Query` 必须搭配 `Sched.Tick()`、`Sched.Render()` 等调度装饰器使用，否则不会执行。

```python
from architect.compact import Query, EntityId, ExtraArguments
from architect.compact import SubsystemServer, ServerSubsystem
from architect.compact import Sched

@SubsystemServer
class QuerySystem(ServerSubsystem):

    # Query 必须与 Sched 装饰器配对使用
    @Sched.Tick()
    @Query(HealthCompServer)
    def onQuery(self, comp):
        # comp 是 HealthCompServer 实例
        print('Health: %d' % comp.health)

    # 同时注入 entityId
    @Sched.Tick()
    @Query(HealthCompServer, EntityId)
    def onQueryWithId(self, comp, entityId):
        print('Entity %s has %d HP' % (entityId, comp.health))

    # 带额外参数
    @Sched.Tick()
    @Query(HealthCompServer, ExtraArguments)
    def onQueryWithArgs(self, comp, args):
        print('Extra args: %s' % str(args))

    # 使用 required/excluded 过滤
    @Sched.Tick()
    @Query(HealthCompServer, required=[AnotherComp], excluded=[BadComp])
    def onFilteredQuery(self, comp):
        pass
```

---

## 9. 远程调用 (RPC)

使用 `@Remote` 装饰器和 `remote` 类。**只需要导入 `Remote` 和 `remote`**。

### 9.1 服务端

```python
from architect.compact import Remote, remote
from architect.compact import SubsystemServer, ServerSubsystem

@SubsystemServer
class RpcSystem(ServerSubsystem):

    @Remote
    def serverGetPlayerName(self, playerId):
        return 'Player_%s' % playerId[:8]

    def someMethod(self):
        # 发送给所有客户端
        remote.client.callEvery('rpc_topic', {'data': 456})

        # 发送给指定客户端
        remote.client.call('player_id', 'rpc_topic', {'data': 123})
```

### 9.2 客户端

```python
from architect.compact import remote
from architect.compact import SubsystemClient, ClientSubsystem

@SubsystemClient
class RpcClient(ClientSubsystem):

    def onJoin(self):
        # 调用服务端的 Remote 方法（无返回值）
        remote.server.call('RpcSystem.serverGetPlayerName')

        # 调用服务端的 Remote 方法并等待返回值
        ftr = remote.server.invoke('RpcSystem.serverGetPlayerName')
ftr.done(lambda name: print('Server says: %s' % name))
```

---

## 10. 响应式 UI

```python
from architect.compact import UiSubsystem, Screen, Hud, Sink, signal, AutoCreate

uiDef = {
    'type': 'stack_panel',
    'size': ['100%', '100%'],
    'controls': [
        {
            'label': 'health_text',
            'type': 'label',
            'text': 'Health: 100',
            'pos': [0, 0],
            'size': ['100%', 20]
        },
        {
            'label': 'heal_btn',
            'type': 'button',
            'text': 'Heal',
            'pos': [0, 30],
            'size': [100, 20]
        }
    ]
}

@Screen
@AutoCreate
class MyScreen(UiSubsystem):

    def onCreate(self):
        # signal() 返回 (getter, setter) 元组
        getHealth, setHealth = signal(100)
        self.getHealth = getHealth
        self.setHealth = setHealth
        self.healthText = self.find('health_text')
        print('UI Screen created')

    # @Sink 装饰器：自动追踪响应式依赖
    @Sink
    def updateHealthLabel(self):
        health = self.getHealth()
        self.healthText.asLabel().SetText('Health: %d' % health)

    def onHeal(self):
        newHealth = min(100, self.getHealth() + 20)
        self.setHealth(newHealth)

    def onDestroy(self):
        print('UI Screen destroyed')
```

---

## 11. 插件系统

```python
from architect.compact import getPlugin, Plugin, PluginBase, hasPlugin

# @Plugin 必须先调用以返回装饰器
@Plugin('MyPlugin', [1, 0, 0], 'AuthorName', 'Description')
class MyPlugin(PluginBase):
    def onAttach(self, manager):
        pass

    def onReady(self, manager):
        pass

# 使用插件
if hasPlugin('other_mod'):
    plugin = getPlugin('other_mod')
    plugin.someMethod()
```

---

## 12. 工具函数

```python
from architect.compact import isServer, levelId
from architect.compact import Sched, defaultFilters

if isServer():
    print('Running on server')

lid = levelId()
print('Level ID: %s' % lid)
```

---

## 完整 API 对照

| 功能 | 导入来源 | `architect.compact` 支持 |
|------|---------|:---:|
| 子系统初始化 | `createServer()`, `createClient()`（无参数，读取 `conf.py`） | ✅ |
| 子系统注册 | `@SubsystemServer`, `@SubsystemClient` | ✅ |
| 子系统基类 | `ServerSubsystem`, `ClientSubsystem` | ✅ |
| 调度装饰器 | `Sched.Tick()`, `Sched.Render()`, `Sched.Fixed()`, `Sched.Event()` | ✅ |
| 组件定义 | `@Component()`, `BaseCompServer`, `BaseCompClient` | ✅ |
| 组件操作 | `createComponent`, `getComponent`, `getEntities`, `hasComponent` | ✅ |
| 原生组件常量 | `NeC`, `NeS`（仅常量名称，不可继承） | ✅ |
| 事件监听 | `@EventListener`, `@CustomEvent`, `ChainedEvent` | ✅ |
| 实体查询 | `@Query`（必须搭配 `@Sched.Tick()` 等使用） | ✅ |
| 远程调用 | `@Remote`, `remote`（`remote.client`/`remote.server`） | ✅ |
| UI 系统 | `UiSubsystem`, `@Screen`, `@Hud`, `@Sink`, `signal()` | ✅ |
| 插件系统 | `@Plugin()`, `PluginBase`, `getPlugin`, `hasPlugin` | ✅ |
| 工具 | `isServer`, `levelId`, `defaultFilters` | ✅ |
| Future/异步 | `Future`, `Async` | ✅ |
| 数学 | `architect.math.vec3`, `architect.math.mat4` | 通过子模块 |