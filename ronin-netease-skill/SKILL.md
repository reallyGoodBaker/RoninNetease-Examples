---
name: ronin-netease
description: RoninNetease框架应用指南 — 基于anim/inputEx/template三个实例项目总结的框架使用方法。适用于网易我的世界Python模组开发（Python 2.7），内容包括：项目初始化、ECS子系统系统、数据资产定义、组件系统、动画/输入插件、事件系统、配置热更新等。
---

# RoninNetease Framework 框架应用指南

本指南基于 `anim`（完整动画系统）、`inputEx`（轻量输入示例）和 `template`（最小模板）三个实例项目，总结 RoninNetease 框架在网易我的世界模组开发中的使用方法。

---

## 快速参考表

| 需求 | 参考项目 | 关键文件 |
|------|----------|----------|
| 最小启动 | template | `conf.py`, `modMain.py`, `__init__.py` |
| 完整项目 | anim | all files in `anim/bp/my_scripts/` |
| 仅客户端 | inputEx | `conf.py`, `__init__.py`, `testClient.py` |
| 动画系统 | anim | `assets/animations.py`, `assets/animMeta.py`, `systems/animPlayer.py` |
| 输入系统 | inputEx | `assets/inputAction.py`, `assets/inputMapping.py`, `testClient.py` |
| 事件系统 | anim | `assets/notifies.py`, `systems/animPlayer.py` |
| ECS组件 | anim | `components/*.py`, `systems/animServer.py` |

---

## 一、项目结构与初始化

### 1.1 最小模板（参考 template）

**conf.py**
```python
# -*- coding: utf-8 -*-
MOD_ENGINE_NAME = "engine/architect"
MOD_SYSTEM_NAME = "my_scripts"
MOD_SERVER_MODULES = ["%s" % MOD_SYSTEM_NAME]
MOD_CLIENT_MODULES = ["%s" % MOD_SYSTEM_NAME]
```

**modMain.py**
```python
# -*- coding: utf-8 -*-
from engine.architect.conf import modConf
from engine.architect.compact import createMod

modConf().value.name = "myMod"
modConf().value.desc = "模块描述"
modConf().value.author = "author"
```

**__init__.py**
```python
# -*- coding: utf-8 -*-
from engine.architect.compact import *
```

### 1.2 完整结构（参考 anim）

```
bp/mod_name/
  conf.py              # 框架配置
  modMain.py           # 入口
  __init__.py          # 子系统注册
  client.py            # 创建客户端
  server.py            # 创建服务端
  assets/              # 数据资产
    __init__.py
    animations.py      # 动画定义
    animMeta.py        # 动画元数据
    inputAction.py     # 输入动作
    inputMapping.py    # 输入映射
    notifies.py        # 通知事件
    networkId.py       # 网络ID
  systems/             # 游戏逻辑
    __init__.py
    animPlayer.py      # 动画播放
    animServer.py      # 动画服务端
  components/          # ECS组件
    __init__.py
```

---

## 二、ECS 子系统系统

### 2.1 注册子系统（__init__.py）

```python
from engine.architect.compact import *
from engine.architect.core.annotation import SubsystemServer, SubsystemClient

@SubsystemClient()
def cs(view):
    view.reg("systems.animPlayer")

@SubsystemServer()
def ss(view):
    view.reg("systems.animServer")
```

### 2.2 创建子系统

**客户端**（参考 `systems/animPlayer.py`）:
```python
from engine.architect.compact import ClientSubsystem

class AnimPlayerSystem(ClientSubsystem):
    def __init__(self):
        ClientSubsystem.__init__(self)
        self.name = "animPlayer"
        self.phase = "Update"  # BeforeUpdate | Update | AfterUpdate

    def init(self, view):
        pass

    def update(self, view):
        pass

    def destroy(self, view):
        pass
```

**服务端**（参考 `systems/animServer.py`）:
```python
from engine.architect.compact import ServerSubsystem

class AnimServerSystem(ServerSubsystem):
    def __init__(self):
        ServerSubsystem.__init__(self)
        self.name = "animServer"

    def init(self, view):
        pass

    def update(self, view):
        pass
```

### 2.3 Phase 说明

| Phase | 顺序 | 用途 |
|-------|------|------|
| `BeforeUpdate` | 第1 | 输入处理、数据准备 |
| `Update` | 第2 | 核心逻辑、动画更新 |
| `AfterUpdate` | 第3 | 后处理 |

---

## 三、数据资产（Assets）

### 3.1 资产基类（参考 `core/asset.py`）

```python
from engine.architect.core.asset import *

class MyAsset(Asset):
    def __init__(self):
        self.id = None
        self.data = {}

    def serialize(self):
        return {"id": self.id, "data": self.data}
```

### 3.2 资产示例

**动画定义**（animations.py）:
```python
class Animations(Asset):
    def __init__(self):
        self.id = None
        self.key_frame = None
        self.duration = 0.0

    def serialize(self):
        return {"id": self.id, "key_frame": self.key_frame, "duration": self.duration}
```

**输入动作**（inputAction.py）:
```python
class InputActions(object):
    ACTION_JUMP = "action_jump"
    ACTION_ATTACK = "action_attack"
```

**通知事件**（notifies.py）:
```python
class Notifies(object):
    ANIM_FINISH = "AnimFinishNotify"
    PLAYER_JOIN = "PlayerJoinNotify"
```

**网络ID**（networkId.py）:
```python
NETWORK_ID_ANIMATION = 1001
NETWORK_ID_INPUT = 1002
```

---

## 四、组件（Components）

### 4.1 定义组件（参考 `component/core.py`）

```python
from engine.architect.component.core import Component

class MyComponent(Component):
    def __init__(self):
        Component.__init__(self)
        self.CompIndex = "my_index"
        self.data = {}
```

### 4.2 使用组件

```python
# 在子系统中获取组件
class MySystem(ClientSubsystem):
    def init(self, view):
        self.engine = view.engine

    def update(self, view):
        entities = self.engine.query("my_index")
        for entity in entities:
            comp = view.entity.get(entity, "MyComponent")
            if comp:
                comp.data["key"] = value
```

---

## 五、插件系统

### 5.1 启用插件（conf.py）

```python
PLUGINS = [
    "engine.architect.plugins.animation",
    "engine.architect.plugins.input",
]
```

### 5.2 动画插件

```python
# 启用后在子系统中使用
class AnimPlayer(ClientSubsystem):
    def init(self, view):
        from engine.architect.plugins.animation.client import AnimClient
        self.animClient = AnimClient(view.engine)

    def play(self, entity_id, anim_name):
        self.animClient.play(entity_id, anim_name, {
            "loop": True,
            "speed": 1.0
        })
```

### 5.3 输入插件（参考 inputEx 插件源码）

```python
from engine.architect.plugins.input.client import InputClient

class InputTest(ClientSubsystem):
    def init(self, view):
        self.inputClient = InputClient(view.engine)
        self.inputClient.regAction("my_action")
        self.inputClient.regKey("my_action", 0x20)
```

---

## 六、事件系统

### 6.1 监听事件

```python
from engine.architect.event.client import EventClient

class MySystem(ClientSubsystem):
    def init(self, view):
        EventClient.listen(self, "OnKeyPressEvent", self.onKeyPress)
        EventClient.listen(self, "MyCustomEvent", self.onCustom)

    def onKeyPress(self, args):
        action = args["action"]

    def onCustom(self, args):
        pass
```

### 6.2 发送事件

```python
from engine.architect.event.core import EventPayload, sendEvent

sendEvent("MyEvent", EventPayload({"key": "value"}))
```

---

## 七、配置热更新

```python
from engine.architect.conf import modConf

# 读取
debug = modConf().value.get("debug", False)

# 子系统监听变化
class MySystem(ClientSubsystem):
    def configChanged(self, view):
        self.debug = modConf().value.get("debug", False)
```

---

## 八、实例项目使用模式总结

| 方面 | anim（完整） | inputEx（轻量） | template（最小） |
|------|-------------|-----------------|-----------------|
| 双端 | client + server | 仅客户端 | client + server |
| assets | 完整（动画/输入/通知） | 仅输入 | 无 |
| systems | animPlayer + animServer | testClient | 无 |
| components | 有 | 无 | 无 |
| plugins | animation + input | input | 无 |
| 启动方式 | client.py / server.py 拆分 | modMain.py 统一 | modMain.py 统一 |

---

## 九、工作流程

1. **创建 conf.py** — 配置框架名称、模块列表、插件列表
2. **创建 modMain.py** — 设置 mod 元信息（name, desc, author）
3. **创建 __init__.py** — 用 `@SubsystemClient()` / `@SubsystemServer()` 注册子系统
4. **实现子类** — 继承 `ClientSubsystem` / `ServerSubsystem`
5. **创建 assets** — 定义数据资产（动画、输入映射等）
6. **创建 components** — 定义 ECS 组件
7. **启动** — 调用 `createClient()` / `createServer()`
