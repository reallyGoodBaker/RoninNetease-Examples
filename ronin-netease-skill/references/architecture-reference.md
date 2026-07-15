# RoninNetease Framework 架构参考

从 anim 项目源码分析提取的框架内部架构详解。

---

## 核心架构

```
┌─────────────────────────────────────────────┐
│              User Code (你的模组)              │
│  conf.py / modMain.py / __init__.py          │
│  systems/ / assets/ / components/           │
├─────────────────────────────────────────────┤
│          Compact API (architect.compact)      │
│  createMod / createClient / createServer      │
│  ClientSubsystem / ServerSubsystem           │
├─────────────────────────────────────────────┤
│           SubsystemManager (管理器)           │
│  子系统注册 / 生命周期管理 / phase 调度        │
├─────────────────────────────────────────────┤
│   architect.core 引擎抽象层                    │
│  loader / basic / annotation / configurator   │
├─────────────────────────────────────────────┤
│       NetEase MC Engine API                   │
│  mod.client.extraClientApi                    │
│  mod.server.extraServerApi                    │
├─────────────────────────────────────────────┤
│         System Plugins                        │
│  event / animation / input / squad           │
└─────────────────────────────────────────────┘
```

---

## 各模块职责

### architect.compact
- `createMod()` — 注册 mod 初始化回调
- `createClient()` / `createServer()` — 创建客户端/服务端系统管理
- `ClientSubsystem` / `ServerSubsystem` — 子系统基类

### architect.core.annotation
- `@SubsystemClient()` / `@SubsystemServer()` — 注册子系统
- `@Query(...)` — 实体查询装饰器
- `@CompIndex(...)` — 组件索引装饰器

### architect.core.asset
- `Asset` — 数据资产基类（含序列化方法）

### architect.core.loader
- 模块 loader，自动扫描注册 subsystems/components/plugins

### architect.core.configurator
- `modConf()` — 全局配置管理器
- 支持运行时热更新配置

### architect.core.subsystem
- SubsystemManager，管理子系统生命周期
- 按 phase（BeforeUpdate / Update / AfterUpdate）调度更新

### architect.component.core
- `Component` — ECS 组件基类
- 支持 CompIndex 反向索引用于快速查询

### architect.event.*
- `EventClient` — 客户端事件监听/发送
- `EventServer` — 服务端事件广播
- `EventPayload` — 事件数据载荷
- 事件链支持 capture / bubble / stop / prevent

---

## 关键约束

- **Python 2.7** — NetEase MC 引擎要求
- **subsystem 必须注册** — 通过 `@SubsystemClient()` / `@SubsystemServer()` 装饰器
- **phase 固定三种** — BeforeUpdate → Update → AfterUpdate
- **assets 需继承 Asset** — 实现 serialize() 方法
- **components 需继承 Component** — 可设置 CompIndex 加速查询
- **视图(view)模式** — 子系统通过 `view.engine` / `view.entity` 操作引擎和实体
