# UI 系统

`architect` 的 UI 系统基于网易 SDK 的 ScreenNode 机制，提供了声明式 UI 定义、响应式数据绑定、手势事件处理等功能。

## UiSubsystem

UI 子系统继承自 `ScreenNode`、`ClientSubsystem` 和 `EventTarget`，是 UI 的核心类：

```python
from architect.ui import UiSubsystem, Sink, AutoCreate, UiDef, signal, reactive, Screen
```

### 定义 UI

```python
@UiDef('netease.my_ui.main')
@Screen
@AutoCreate
class MyUI(UiSubsystem):
    ns = 'my_namespace'

    def onCreate(self):
        print("UI created")

    def onDestroy(self):
        print("UI destroyed")
```

### 生命周期

1. **`Create()`**: UI 创建时自动调用，初始化根控件、监听返回键、初始化 Sink 和手势
2. **`Destroy()`**: UI 销毁时自动调用，清理监听器和 Sink
3. **`onCreate()`**: 重写此方法进行初始化
4. **`onDestroy()`**: 重写此方法进行清理
5. **`onBackPressed()`**: 返回键按下时调用，返回 `True` 阻止默认关闭行为

### 创建与管理

```python
# 获取或创建 UI 实例
ui = MyUI.getOrCreate()

# 强制创建新实例（替换旧实例）
ui = MyUI.create()

# 压栈（Screen 模式）
ui = MyUI.pushScreen()

# 移除 UI
ui.remove()
```

## 控件查找

```python
# 通过路径查找（带缓存）
ctrl = self.find('path/to/control')

# 通过名称查找（从根控件开始）
ctrl = self.findByName('control_name')
```

## 响应式数据绑定

### `signal`

创建响应式数据变量（返回 (getter, setter) 元组）：

```python
from architect.ui import signal

class MyUI(UiSubsystem):
    def onCreate(self):
        self.count, self.setCount = signal(0)

    @Sink
    def update_label(self):
        # 自动追踪依赖，count 变化时自动重新执行
        self.find('label').asText().SetText(f"Count: {self.count()}")
```

### `reactive`

将整个对象变为响应式：

```python
from architect.ui import reactive

class MyUI(UiSubsystem):
    def onCreate(self):
        data = MyData()
        self.getData, self.setData = reactive(data)
        # 修改 data 的任何字段都会触发依赖更新
```

## 装饰器

### `@UiDef(uiDef)`

标记 UI 的 JSON 定义路径，框架会自动注册 UI：

```python
@UiDef('netease.my_ui.main')
class MyUI(UiSubsystem):
    pass
```

### `@AutoCreate`

标记 UI 在游戏加载完成后自动创建：

```python
@AutoCreate
class MyUI(UiSubsystem):
    pass
```

### `@Screen`

标记 UI 为 Screen 模式（栈式管理）：

```python
@Screen
@AutoCreate
class MyUI(UiSubsystem):
    pass
```

### `@Sink`

标记方法为依赖追踪函数，在控件初始化和依赖变化时自动调用：

```python
@Sink
def update_view(self):
    text = self.find('text')
    text.asText().SetText(f"Value: {self.value()}")
```

## 手势事件

使用 `Touch` 类的装饰器属性绑定手势事件：

```python
from architect.ui import Touch

class MyUI(UiSubsystem):
    @Touch.Click('path/to/button')
    def on_click(self, ev):
        print("Clicked at:", ev.pos)
        print(ev.x, ev.y)
        print("Target:", ev.target)
        print("Control:", ev.control)
```

### 可用手势

| 装饰器 | 说明 |
|--------|------|
| `Touch.Click(btnPath)` | 点击（触摸抬起） |
| `Touch.Down(btnPath)` | 按下 |
| `Touch.Move(btnPath)` | 触摸移动 |
| `Touch.MoveIn(btnPath)` | 移入目标区域 |
| `Touch.MoveOut(btnPath)` | 移出目标区域 |
| `Touch.Cancel(btnPath)` | 触摸取消 |

### 事件对象属性

每个手势回调接收的 `ev` 对象包含：

- **`ev.target`**: 绑定的控件对象
- **`ev.control`**: 路径对应的控件
- **`ev.screen`**: UI 实例
- **`ev.x` / `ev.y`**: 触摸坐标
- **`ev.pos`**: `(x, y)` 坐标元组

## 命名空间

UI 命名空间默认为 `UI_NAMESPACE`，可通过类属性覆盖：

```python
class MyUI(UiSubsystem):
    ns = 'my_custom_namespace'