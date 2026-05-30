# FSM 有限状态机

`architect.fsm` 提供了有限状态机（Finite State Machine）实现，用于管理实体的状态切换。

## FSM 类

```python
from architect.fsm import FSM
```

### 构造函数

```python
fsm = FSM(owner, initialState, states)
```

- **`owner`**: FSM 所属的对象（如子系统或实体）
- **`initialState`**: 初始状态名称
- **`states`**: 字典，key 为状态名，value 为状态配置

### 状态配置

每个状态可以定义 `accept` 和 `enter`/`exit` 回调：

```python
states = {
    'Idle': {
        'accept': ['Patrol', 'Attack'],   # 可接受的事件名列表
        'enter': lambda owner: print('Enter Idle'),
        'exit': lambda owner: print('Exit Idle'),
    },
    'Patrol': {
        'accept': ['Idle', 'Attack'],
        'enter': on_enter_patrol,          # 函数引用
    },
    'Attack': {
        'accept': ['Idle'],
    },
}

fsm = FSM(entity, 'Idle', states)
```

### 核心方法

```python
# 发送事件给 FSM，触发状态切换
fsm.accept(eventName, *args, **kwargs)

# 获取当前状态名称
current = fsm.current  # 属性访问

# 判断当前是否为指定状态
if fsm.isState('Idle'):
    print('Currently Idle')
```

### 回调

每个状态配置支持以下回调：

| 回调 | 调用时机 | 签名 |
|------|---------|------|
| `enter` | 进入该状态时 | `enter(owner, *args, **kwargs)` |
| `exit` | 离开该状态时 | `exit(owner, *args, **kwargs)` |

`*args` 和 `**kwargs` 来自 `accept()` 调用时传入的参数。

### 完整示例

```python
from architect.fsm import FSM

class Monster:
    def __init__(self):
        states = {
            'Idle': {
                'accept': ['Patrol', 'Attack'],
                'enter': lambda self: print('Monster is idle'),
                'exit': lambda self: print('Monster stops idling'),
            },
            'Patrol': {
                'accept': ['Idle', 'Attack'],
                'enter': self.on_start_patrol,
            },
            'Attack': {
                'accept': ['Idle'],
                'enter': lambda self, target: print('Attacking %s' % target),
            },
        }
        self.fsm = FSM(self, 'Idle', states)

    def on_start_patrol(self):
        print('Monster starts patrolling')

    def update(self):
        if self.fsm.isState('Idle'):
            self.fsm.accept('Patrol')
        elif self.fsm.isState('Patrol'):
            self.fsm.accept('Attack', 'player_1')

# 使用
monster = Monster()
monster.fsm.accept('Patrol')           # Idle -> Patrol
monster.fsm.accept('Attack', 'p1')     # Patrol -> Attack
print(monster.fsm.current)             # 'Attack'
```

## 已废弃：Statetree

`architect.fsm.stateTree` 是旧版的状态树实现，已被 `FSM` 替代。新代码请使用 `FSM` 类。