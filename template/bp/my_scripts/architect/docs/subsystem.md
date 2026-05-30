# Subsystem 子系统

`architect` 的核心组织单位是 Subsystem（子系统），每个子系统负责特定的功能逻辑。

## 生命周期

Subsystem 定义了清晰的初始化顺序：

1. **`__init__`** - 构造函数，接收底层引擎系统实例
2. **`onInit()`** - 子系统创建完毕后调用（在 `_init()` 中自动调用）
3. **`onReady()`** - 所有子系统初始化完毕后调用，此时可安全获取其他子系统
4. **`onUpdate(dt)`** - 每 Tick 调用，需设置 `self.canTick = True`
5. **`onRender(dt)`** - 每渲染帧调用（仅 `ClientSubsystem`）
6. **`onDestroy()`** - 子系统销毁时调用

## 定义子系统

使用 `@SubsystemServer` 或 `@SubsystemClient` 装饰器标记子系统类：

```python
from architect.core.subsystem import SubsystemServer, ServerSubsystem

@SubsystemServer
class MySystem(ServerSubsystem):
    def onInit(self):
        print("Server Subsystem initialized")

    def onReady(self):
        other = self.getSubsystem(OtherSystem)
        print("Other system is ready:", other)
```

### 属性

- **`system`**: 底层引擎系统实例（`_ShadowSystemServer` 或 `_ShadowSystemClient`）
- **`engine`**: 引擎命名空间
- **`sysName`**: 系统名称
- **`ticks`**: 子系统被更新的次数
- **`canTick`**: 是否允许 `onUpdate` 调用（默认 False）
- **`initialized`**: 初始化状态标记

## 获取子系统实例

```python
# 通过类获取子系统
target = SubsystemManager.getInstance().getSubsystem(MySystem)

# 通过名称获取
target = SubsystemManager.getInstance().getSubsystemByName('MySystem')

# 类方法获取单例（内部调用 getSubsystem）
inst = MySystem.getInstance()
```

## 事件监听

Subsystem 提供两组事件监听方法：

```python
# 监听自定义事件（默认 isCustomEvent=True）
self.on('MyEvent', self.my_handler)

# 取消监听自定义事件
self.off('MyEvent', self.my_handler)

# 监听引擎原生事件（isCustomEvent=False）
self.listen('PlayerJoinEvent', self.on_player_join)

# 取消监听引擎事件
self.unlisten('PlayerJoinEvent', self.on_player_join)
```

## 广播事件

```python
self.broadcast('EventName', {'key': 'value'})
```

## 装饰器事件监听

在 Subsystem 中可以直接使用 `@EventListener` 或 `@CustomEvent` 装饰方法：

```python
from architect.event import EventListener, CustomEvent

class MySystem(ServerSubsystem):
    @EventListener('PlayerJoinEvent')
    def on_player_join(self, ev):
        # ev 是 ChainedEvent 实例，通过属性访问
        playerId = ev.id
        print("Player joined:", playerId)

    @CustomEvent('MyEvent')
    def on_my_event(self, ev):
        # ev 是 ChainedEvent 实例
        print("Custom event:", ev.eventType)
```

## 服务端子系统的特有功能

`ServerSubsystem` 提供了向客户端发送数据的方法：

```python
# 向指定客户端发送（单个玩家）
self.sendClient(playerId, 'EventName', data)

# 向多个客户端发送
self.sendClient([playerId1, playerId2], 'EventName', data)

# 向所有客户端广播
self.sendAllClients('EventName', data)

# 生成实体（通过类型字符串或 NBT 字典）
eid = self.spawnEntity('minecraft:zombie', location, (0, 0))
# 或通过 NBT
eid = self.spawnEntity({'nbt': 'data'}, location, (0, 0), isNpc=False, isGlobal=False)

# 销毁实体
self.destroyEntity(eid)

# 生成物品实体
self.spawnItem(itemDict, location)
```

## 客户端子系统的特有功能

`ClientSubsystem` 提供了渲染帧和特效相关的方法：

```python
# 向服务端发送事件
self.sendServer('EventName', data)

# 生成客户端实体
self.spawnEntity('minecraft:sheep', (0, 0, 0), (0, 0))

# 创建特效/粒子
self.createSfx('path/to/sfx', pos)
self.createParticle('path/to/particle', pos)
self.createEffectBind('path/to/effect', entityId, 'animation')

# 销毁特效
self.destroySfx(entityId)

# 渲染帧回调（需设置 canTick = True）
def onRender(self, dt):
    pass
```

## 静态辅助方法 `subsystem`

在不方便获取子系统实例的场合使用：

```python
from architect.core.subsystem import subsystem

# 客户端→服务端通信
subsystem.sendServer('EventName', data)

# 服务端→客户端通信
subsystem.sendClient(playerId, 'EventName', data)
subsystem.sendAllClients('EventName', data)

# 生成实体
subsystem.spawnServerEntity(template, location, rot)
subsystem.spawnClientEntity(template, pos, rot)
subsystem.spawnItem(itemCls, *args, **kwargs)

# 监听事件
subsystem.addListener('EventName', handler, isCustomEvent=False)
subsystem.removeListener('EventName', handler, isCustomEvent=False)
```

## 固定频率调度器

```python
# 启动固定频率调度器（在 onReady 中调用）
self.scheduleFixed('myScheduler', period=1.0)

# 停止调度器
self.stopFixed('myScheduler')