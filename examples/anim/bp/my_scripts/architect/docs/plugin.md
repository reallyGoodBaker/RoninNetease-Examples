# 插件系统 (architect.plugins)

`architect.plugins` 提供了插件/模组间的模块加载和依赖管理机制。

## 核心组件

### 插件管理器 (PluginManager)

由框架自动管理，负责插件的注册、依赖解析和执行生命周期回调。

### 装饰器

#### `@Plugin(name, version, author, description)`

将类注册为插件。必须使用函数调用形式。

```python
from architect.compact import Plugin, PluginBase

@Plugin('MyPlugin', [1, 0, 0], 'AuthorName', 'A sample plugin')
class MyPlugin(PluginBase):
    def __init__(self):
        self.data = {}

    def onAttach(self, manager):
        # 插件被挂载时调用
        print('MyPlugin attached')

    def onReady(self, manager):
        # 所有插件加载完成后调用
        print('MyPlugin ready')
```

参数说明：
- `name`（str）: 插件唯一名称，用于 `getPlugin()` 查询
- `version`（list[int]）: 语义化版本号 `[major, minor, patch]`
- `author`（str）: 作者名称
- `description`（str）: 插件描述

### 基类

#### `PluginBase`

所有插件的基类，提供生命周期方法：

```python
class PluginBase:
    def __init__(self):
        pass

    def onAttach(self, manager):
        # 当插件被挂载到管理器时调用
        pass

    def onReady(self, manager):
        # 当所有插件都完成 onAttach 后调用
        pass
```

### 核心函数

```python
from architect.compact import getPlugin, hasPlugin

# 获取已注册的插件实例
plugin = getPlugin('MyPlugin')
if plugin:
    plugin.do_something()

# 检查插件是否存在
if hasPlugin('other_mod'):
    print('other_mod is loaded')
```

### 使用示例

#### 定义插件

```python
from architect.compact import Plugin, PluginBase

@Plugin('my_weapon_mod', [1, 2, 0], 'DevTeam', 'Custom weapon system')
class WeaponPlugin(PluginBase):
    def __init__(self):
        self.weapons = {}

    def onAttach(self, manager):
        self.weapons = {'sword': 10, 'bow': 8}

    def onReady(self, manager):
        print('Weapon system ready')

    def getDamage(self, weaponName):
        return self.weapons.get(weaponName, 0)
```

#### 使用插件

```python
from architect.compact import getPlugin, hasPlugin

# 在子系统或组件中使用
class GameSystem:
    def onInit(self):
        if hasPlugin('my_weapon_mod'):
            plugin = getPlugin('my_weapon_mod')
            damage = plugin.getDamage('sword')
            print('Damage: %d' % damage)
```

---

## 完整 API 对照

| 功能 | API | 说明 |
|------|-----|------|
| 插件注册 | `@Plugin(name, version, author, desc)` | 装饰器-注册插件类 |
| 插件基类 | `PluginBase` | 插件的基类（含 onAttach/onReady） |
| 获取插件 | `getPlugin(name)` | 通过名称获取插件实例 |
| 检查插件 | `hasPlugin(name)` | 检查插件是否已加载 |