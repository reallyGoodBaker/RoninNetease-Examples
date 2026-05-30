# 事件系统

`architect` 提供了一套灵活的事件系统，支持引擎原生事件和自定义事件的监听与广播。

## 架构概览

事件系统由以下核心组件构成：

- **`Delegate`**: 委托，封装单个可调用对象，通过 `bind`/`unbind`/`call` 管理
- **`EventSignal`**: 事件信号，轻量级发布/订阅机制，支持 `on`/`off`/`emit`
- **`EventTarget`**: 事件目标，提供 `addListener`/`removeListener`/`dispatch` 的事件管理基类
- **`EventChain`**: 事件链，管理同一事件类型的多个监听器，支持捕获/冒泡顺序和中断
- **`ChainedEvent`**: 链式事件对象，封装事件数据，支持 `stop()`/`prevent()` 等操作
- **`EventListener`**: 装饰器，标记方法为事件监听器
- **`CustomEvent`**: 装饰器，标记方法为自定义事件监听器

## 事件信号 `EventSignal`

`EventSignal` 是轻量级的信号/槽机制，可以作为属性装饰器使用：

```python
from architect.event import EventSignal

signal = EventSignal()

def handler():
    print("Signal emitted!")

# 监听信号
signal.on(handler)

# 触发信号
signal.emit()

# 取消监听
signal.off(handler)
```

## 事件目标 `EventTarget`

`EventTarget` 提供封装的事件管理能力，适合作为基类使用：

```python
from architect.event import EventTarget

class MyClass(EventTarget):
    def __init__(self):
        EventTarget.__init__(self)
        self.addListener('SomeEvent', self.on_event)

    def on_event(self, *args):
        print("Event received:", args)

    def cleanup(self):
        self.removeAllListener()
```

### EventTarget 方法

- **`addListener(event, handler)`**: 监听事件
- **`removeListener(event, handler)`**: 取消监听
- **`removeAllListener()`**: 移除所有监听器
- **`dispatch(event, *args)`**: 广播事件

## 事件链 `EventChain`

通过 `event()` 函数获取事件链实例：

```python
from architect.event.server import event as serverEvent
from architect.event.client import event as clientEvent

# 服务端事件链
ev = serverEvent('PlayerJoinEvent')

# 自定义事件
ev = clientEvent('MyCustomEvent', isCustomEvent=True)
```

### EventChain API

```python
chain = event('EventName', isCustomEvent=False)

# 添加监听器（冒泡顺序）
chain.addListener(lambda ev: print("Event fired:", ev))

# 添加监听器（捕获顺序）
chain.capture(lambda ev: print("Capture:", ev))

# 移除监听器
fn = lambda ev: print("remove me")
chain.addListener(fn)
chain.removeListener(fn)

# 分发事件（接收 dict 数据）
chain.dispatch({"key": "value"})

# 属性控制
chain.guarded = True       # 出错后是否阻止后续监听器
chain.useCapture = False   # True=添加顺序, False=反向顺序
```

### 链式事件对象 `ChainedEvent`

事件分发时自动创建 `ChainedEvent` 实例并传入监听器：

```python
def my_handler(ev):
    print(ev.eventType)       # 事件类型名称
    print(ev.dict())          # 事件数据字典

    ev.stop()                 # 停止事件继续传递
    ev.prevent()              # 阻止默认行为（设置 cancel=True）

    ev.setEvent('key', 'val')  # 设置事件数据
    ev.updateEvent({'a': 1})   # 批量更新事件数据
```

## 服务端/客户端事件管理器

### 服务端 `ServerEvents`

```python
from architect.event.server import ServerEvents

chain = ServerEvents.getOrCreateChain('EventName', isCustomEvent=False)
chain.addListener(my_handler)
```

### 客户端 `ClientEvents`

```python
from architect.event.client import ClientEvents

chain = ClientEvents.getOrCreateChain('EventName', isCustomEvent=True)
chain.addListener(my_handler)
```

## 装饰器风格的事件监听

### `@EventListener`

标记方法接收引擎原生事件：

```python
from architect.event import EventListener

class MySystem(ServerSubsystem):
    @EventListener('PlayerJoinEvent')
    def on_player_join(self, ev):
        print("Player joined:", ev)
```

### `@CustomEvent`

标记方法接收自定义事件（等价于 `@EventListener(eventType, isCustomEvent=True)`）：

```python
from architect.event import CustomEvent

class MySystem(ServerSubsystem):
    @CustomEvent('MyCustomEvent')
    def on_my_event(self, ev):
        print("Custom event received:", ev)
```

## 委托 `Delegate`

`Delegate` 封装单个可调用对象，不安全地处理异常：

```python
from architect.event import Delegate

del = Delegate()

def my_fn(*args):
    print("Called with:", args)

# 绑定
del.bind(my_fn)

# 调用
del("hello")  # 或 del.call("hello")

# 解绑
del.unbind()