# 状态树 (architect.fsm.stateTree)

树形有限状态机，比传统 FSM 灵活性稍低但更易于模块化。将状态组织成树结构，支持自动搜索可进入的叶子节点、沿路径切换、向上回溯等能力。

## 核心概念

状态树将状态组织为一棵**多叉树**：
- **叶子节点**：真正的"状态"，每帧只能激活一个叶子节点
- **非叶子节点**：作为"分类/分组"，不执行逻辑，但可以控制子树整体的进入/退出条件
- **搜索算法**：每帧自动沿树向下搜索第一个可进入的叶子节点，找不到则向上回溯
- **激活路径**：当前激活的叶子节点 + 其所有祖先节点构成"激活路径"，路径上所有节点的 `update()` 都会被调用

## StateTree

状态树的核心类，继承自 `Unreliable`（异常安全）：

```python
from architect.fsm.stateTree.common import StateTree, StateNode
```

### 树结构管理

```python
tree = StateTree(entityId)

# 创建根节点（默认名为 'root'）
root = tree.getRoot()

# 创建新节点并插入
node = StateNode('attack')
tree.insertNode(node, parent=root)

# 创建匿名节点
node = tree.createNode(parent=root)

# 查找节点
node = tree.findNamedNode('attack')
```

### 节点替换

```python
# 替换节点
tree.replaceNode(oldNode, newNode)
tree.replaceNamedNode('attack', newAttackNode)

# 替换根节点
newRoot = StateNode('newRoot')
tree.replaceNode(None, newRoot)
# 等价于
tree.setRoot(newRoot)
```

### 状态执行

```python
# 每帧调用：搜索下一个叶子节点并切换
tree.execute()

# 强制切换到指定节点（跳过搜索）
tree.switchNode(targetNode)

# 重置状态
tree.reset()                   # 重置到初始状态
tree.reset(clearMapping=True)  # 重置并清空映射
```

### 状态查询

```python
# 当前状态
current = tree.getCurrent()
current = tree.currentState()
name = tree.currentStateName()

# 检查是否已完成（即没有激活的叶子节点）
if tree.isFinished():
    pass

# 获取当前激活路径上的所有节点（从根到当前叶子）
activeNodes = tree.findAllActivatedStateNodes()
```

### 内部搜索算法

`searchNode()` 的搜索逻辑：

1. **无当前节点** → 从根节点开始深度优先搜索第一个可进入的叶子
2. **当前是叶子** → 先搜索同级兄弟节点，找不到则向上回溯到父节点继续搜索兄弟子树
3. **当前是非叶子** → 继续向下搜索子节点中的叶子
4. 如果某个祖先的 `canEnter()` 返回 `False`，则跳过它继续向上
5. 每步都会检查 `canEnter()` / `canExit()` 条件

每次 `execute()` 调用流程：
1. 调用所有激活路径上节点的 `update(tree)`
2. 调用 `searchNode()` 搜索下一个可进入的叶子
3. 如果找到，沿路径依次 `exit` 当前节点 → `enter` 路径上的所有节点 → 最终到达目标叶子

## StateNode

状态节点，可包含子节点形成树结构：

```python
class StateNode:
    def __init__(self, name='unknown'):
        pass
```

### 生命周期钩子

```python
class MyNode(StateNode):
    def canEnter(self, tree):
        """是否允许进入此节点（包括其子树）"""
        return True

    def canExit(self, tree):
        """是否允许退出此节点"""
        return True

    def enter(self, previous, tree):
        """进入时回调
        Args:
            previous: 前一个叶子节点
            tree: 状态树实例
        """

    def exit(self, nextNode, tree):
        """退出时回调
        Args:
            nextNode: 下一个叶子节点
            tree: 状态树实例
        """

    def update(self, tree):
        """每帧更新回调（仅在激活路径上时调用）"""
```

### 树操作

```python
node = StateNode('parent')

# 添加子节点
child1 = StateNode('child1')
child2 = StateNode('child2')
node.addChildren(child1, child2)

# 移除子节点
node.removeChild(child1)

# 在指定位置插入
node.insert(0, newChild)

# 替换子节点
node.replaceChild(oldNode, newNode)

# 查找子节点（递归）
found = node.findNamedNode('child2')
```

### 上下文（Context）

节点支持键值对上下文，子节点可以继承父节点的上下文：

```python
root = StateNode('root')
root.setContext('speed', 10)
root.setContext('damage', 50)

child = StateNode('child')
root.addChildren(child)

# 子节点可以获取父节点的上下文
print(child.getContext('speed'))   # 10 （从父节点继承）
print(child.getContext('damage'))  # 50 （从父节点继承）

# 子节点也可以覆盖
child.setContext('speed', 20)
print(child.getContext('speed'))   # 20 （覆盖父节点值）
```

### 节点复制

```python
original = MyCustomNode('test')
original.setContext('key', 'value')

# 深复制（递归复制所有子节点）
copy = original.copy(deep=True)

# 浅复制（只复制当前节点，不含子节点）
shallow = original.copy(deep=False)
```

复制规则：
- 保留 `_parent` 和 `children` 之外的所有实例属性
- 子类的自定义属性也会被复制
- 返回的节点是完全独立的树根（`_parent = None`）

## StateNodeServer（服务端扩展）

服务端专用的节点类，提供引擎操作封装：

```python
from architect.fsm.stateTree.server import StateNodeServer

class MyServerNode(StateNodeServer):
    def __init__(self, name, subsystem=None):
        StateNodeServer.__init__(self, name, subsystem)
```

### 实体变体控制

```python
class MyNode(StateNodeServer):
    def enter(self, previous, tree):
        # 设置实体 MarkVariant
        self.markVariant(tree.entityId, 2)

    def exit(self, nextNode, tree):
        # 获取实体当前 MarkVariant
        variant = self.markVariant(tree.entityId)
```

### 音效播放

```python
class MyNode(StateNodeServer):
    def enter(self, previous, tree):
        # 在实体位置播放音效
        self.playSound(tree.entityId, 'minecraft:entity.player.attack')
```

### 移动控制

```python
class MyNode(StateNodeServer):
    def enter(self, previous, tree):
        # 禁用实体移动
        self.movement(tree.entityId, enabled=False)
        # 启用实体移动
        self.movement(tree.entityId, enabled=True)
```

对玩家使用 `inputpermission` 指令控制；对非玩家实体则调整 `AttrType.SPEED`。

### 摄像机控制

```python
class MyNode(StateNodeServer):
    def enter(self, previous, tree):
        # 禁用摄像机控制
        self.camera(tree.entityId, enabled=False)
        # 启用摄像机控制
        self.camera(tree.entityId, enabled=True)
```

使用 `inputpermission camera` 指令控制。

### 快速创建子节点

```python
class MyNode(StateNodeServer):
    def enter(self, previous, tree):
        # 创建子节点（自动设置 subsystem 和父引用）
        child = self.createChild('sub_state', MyChildNode)
```

## ECS 组件集成

状态树通过 ECS 组件与子系统集成，在 `onUpdate` 中每帧自动调用 `execute()`：

```python
from architect.fsm.stateTree.server import StateTreeCompServer
from architect.fsm.stateTree.client import StateTreeCompClient

# 服务端：为实体附加状态树组件
# 在组件的 onCreate 中自动注册到子系统

# 启用/禁用状态树执行
comp.enabled = True   # 开始执行
comp.enabled = False  # 暂停执行
```

## 完整示例

```python
from architect.fsm.stateTree.common import StateTree, StateNode
from architect.fsm.stateTree.server import StateNodeServer

# 定义状态节点
class IdleNode(StateNode):
    def enter(self, previous, tree):
        print(f'Entity {tree.entityId}: Enter idle')

    def update(self, tree):
        print(f'Idle tick {tree.stateTicks}')

    def canExit(self, tree):
        # 在 idle 停留至少 10 tick 后才能退出
        return tree.stateTicks >= 10

class PatrolNode(StateNode):
    def enter(self, previous, tree):
        print(f'Entity {tree.entityId}: Start patrol')

    def update(self, tree):
        print(f'Patrol tick {tree.stateTicks}')

    def canExit(self, tree):
        return tree.stateTicks >= 20

class ChaseNode(StateNode):
    def enter(self, previous, tree):
        print(f'Entity {tree.entityId}: Chase!')

    def update(self, tree):
        print(f'Chase tick {tree.stateTicks}')

# 构建状态树
tree = StateTree(entityId)

root = tree.getRoot()
action = StateNode('action')
tree.insertNode(action, root)

tree.insertNode(IdleNode('idle'), action)
tree.insertNode(PatrolNode('patrol'), action)
tree.insertNode(ChaseNode('chase'), action)

# 启用并开始执行
comp = tree  # 如果是通过 ECS 组件
comp.enabled = True

# 每帧主动调用（如果使用了 ECS 组件则自动调用）
tree.execute()
```

## 与 FSM 的区别

| 特性 | FSM (`architect.fsm`) | StateTree (`architect.fsm.stateTree`) |
|------|----------------------|--------------------------------------|
| 结构 | 扁平状态列表 | 树形状态层级 |
| 状态切换 | 手动调用 `transitionTo` | 自动搜索可进入的叶子节点 |
| 分组能力 | 无 | 非叶子节点可分组控制 |
| 条件检测 | 在切换时检查 | 每帧自动搜索 |
| 上下文继承 | 无 | 父子节点上下文链 |
| 复杂度 | 更灵活 | 更模块化 |