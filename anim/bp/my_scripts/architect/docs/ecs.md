# 组件系统

`architect` 的组件系统基于网易 SDK 的 `RegisterComponent` / `CreateComponent` 机制，提供声明式组件定义、生命周期管理和查询支持。

## 组件基类

服务端和客户端各有对应的基类：

```python
from architect.component import BaseCompServer, BaseCompClient

# 服务端组件
class MyServerComp(BaseCompServer):
    def onCreate(self, entityId):
        self.data = 0

    def onDestroy(self, entityId):
        pass

    def loadData(self, entityId):
        pass

# 客户端组件
class MyClientComp(BaseCompClient):
    def onCreate(self, entityId):
        pass

    def onDestroy(self, entityId):
        pass

    def loadData(self, entityId):
        pass
```


## 组件创建与管理 API

```python
from architect.component.core import (
    createComponent,
    createComponents,
    createSingletonComponent,
    destroyComponent,
    getOneComponent,
    getOneSingletonComponent,
    getOrCreateComponent,
    getOrCreateSingletonComponent,
    getComponent,
    getComponentWithQuery,
    getEntities,
    hasComponent,
    removeComponents,
)

# 创建组件
comp = createComponent(entityId, MyComponent)

# 批量创建
comps = createComponents(entityId, CompA, CompB)

# 创建单例组件（绑定在 singletonId() 上）
singleton = createSingletonComponent(MyComponent)

# 获取组件的第一个实例
comp = getOneComponent(entityId, MyComponent)

# 获取单例组件
comp = getOneSingletonComponent(MyComponent)

# 获取或创建
comp = getOrCreateComponent(entityId, MyComponent)

# 获取/创建单例
s = getOrCreateSingletonComponent(MyComponent)

# 获取多个组件（仅当实体拥有所有指定组件时才返回列表，否则返回 None）
result = getComponent(entityId, [CompA, CompB])
# 返回 [CompA实例, CompB实例] 或 None

# 带过滤条件的获取
comp = getComponentWithQuery(entityId, targets=[CompA], required=[ReqComp], excluded=[ExcludeComp])

# 检查实体是否拥有所有指定组件
has = hasComponent(entityId, CompA, CompB)

# 销毁组件
destroyComponent(entityId, MyComponent)

# 批量销毁
removeComponents(entityId, CompA, CompB)
```

## 组件标记系统

框架使用 `Marker` 类标记拥有组件的实体：

```python
from architect.component.core import entitiesServer, entitiesClient

# 获取所有有组件的实体 ID
entityIds = getEntities()
```

## 通过字符串名称获取组件

```python
# 名称前加 '#' 前缀获取引擎原生组件
comp = getOneComponent(entityId, '#Attr')

# 直接通过自定义组件名称字符串获取
comp = getOneComponent(entityId, 'MyComponent')
```

## 持久化组件

```python
from architect.component.persistent import PersistKeys

@Component(persist=True)
@PersistKeys('score', 'level', isGlobal=False)
class PlayerDataComponent(BaseCompServer):
    pass
```

持久化会自动将声明字段的 getter/setter 替换为数据库读写：

```python
# isGlobal=False -> ClientKVDatabase
# isGlobal=True  -> ClientKVDatabaseGlobal
```

## 引擎原生组件快捷访问

通过 `NeS`（服务端）和 `NeC`（客户端）访问引擎原生组件：

```python
from architect.component.common import NeS, NeC

# 通过 getOneComponent 获取原生组件
attrComp = getOneComponent(playerId, '#Attr')  # 等价于 compServer.CreateAttr(playerId)
posComp = getOneComponent(entityId, '#Pos')    # 等价于 compClient.CreatePos(entityId)
```

## 查询系统

`@Query` 注解配合调度注解使用，自动筛选实体并注入组件：

```python
from architect.core.scheduler import Scheduler
from architect.query import Query

class MySystem(ServerSubsystem):
    @Sched.Tick()
    @Query(EntityId, MyComponent)
    def handle_logic(self, entityId, myComp):
        pass

    @Query(MyComponent, required=[RequiredComp], excluded=[ExcludeComp])
    def handle_filtered(self, myComp):
        pass
```

### 内置伪组件

- **`EntityId`**: 注入当前实体的 ID 字符串
- **`ExtraArguments`**: 调用时的位置参数列表
- **`ExtraArgDict`**: 调用时的关键字参数字典

### 查询缓存

```python
from architect.query.queryServer import QueryServer

# 缓存组件查询（减少重复创建开销）
pos = QueryServer.cache('pos', entityId, lambda: getOneComponent(entityId, '#Pos'))