# 调度器 Scheduler

`architect` 的调度器提供了灵活的任务调度机制，支持普通任务、可暂停任务（协程）和调度序列。

## 核心类

### Scheduler

调度器管理多个任务队列，每个队列对应一个调度阶段（flag）。任务按阶段依次执行。

```python
from architect.core.scheduler import Scheduler

scheduler = Scheduler()

# 默认执行顺序
print(scheduler.scheduleSequence)
# ('BeforeUpdate', 'Update', 'AfterUpdate')
```

### SchedulerPoller

可轮询的调度器封装，`SimpleFixedScheduler` 是其子类，提供固定频率执行：

```python
from architect.core.scheduler import SimpleFixedScheduler

poller = SimpleFixedScheduler(period=1)

# 启动轮询
poller.start(lambda: print("tick"))

# 更新（在 Tick 中调用）
poller.update()

# 停止
poller.stop()
```

## 添加任务

### 普通任务

```python
def my_task(*args):
    print("Task executed with:", args)

scheduler.addTask('Update', my_task)
```

### 可暂停任务（协程）

使用生成器函数，`yield` 时暂停，下次调用从暂停处继续：

```python
def my_coroutine():
    print("Step 1")
    yield
    print("Step 2")
    yield
    print("Step 3")

scheduler.addSuspendableTask('Update', my_coroutine)
```

## 执行任务

```python
# 执行单个阶段的队列
scheduler.execute('Update', args=[1, 2, 3])

# 执行完整序列（按 scheduleSequence 顺序）
dt, skipped = scheduler.executeSequence()
```

### 执行序列返回值

- **deltaTime**: 距上次执行的时间差（秒）
- **skippedUpdates**: 跳过的更新次数（当 deltaTime 超过阈值时）

## 移除任务

```python
# 移除指定任务
scheduler.removeTask('Update', taskId=123)

# 移除某个阶段的所有任务（taskId=-1）
scheduler.removeTask('Update')

# 在任务执行中标记移除（延迟删除，避免迭代器异常）
from architect.core.scheduler import Scheduler
scheduler.removeTask('Update', taskId)

# 或调用 removeTaskByFn
scheduler.removeTaskByFn(my_function, 'Update')
```

## 内部辅助类

### Task

封装一个可调用对象：

```python
from architect.core.scheduler import Task

task = Task(lambda: print("task"))
print(task.id)  # 自动递增的 ID
print(task.finished)  # False
```

### SuspendableTask

封装一个生成器，每次 `callOnce()` 执行到下一个 `yield`：

```python
task = SuspendableTask(lambda: (print("a") for _ in range(1)))
task.callOnce()  # 执行到 yield 或结束
print(task.finished)  # 如果生成器耗尽则为 True
```

## 与 Subsystem 集成

在 `ServerSubsystem` / `ClientSubsystem` 中通过 `system` 访问调度器：

```python
class MySystem(ServerSubsystem):
    def onReady(self):
        self.system.addSchedulerTask(self.update)

    def update(self):
        print("Tick update")
```

框架提供的 `scheduleFixed` / `stopFixed` 简化了固定频率调度器的使用：

```python
class MySystem(ServerSubsystem):
    def onReady(self):
        self.scheduleFixed('myTask', period=1.0)

    def stop(self):
        self.stopFixed('myTask')
```

## 调度标记常量

调度阶段标记在 `architect.conf` 中定义：

```python
from architect.conf import (
    TIMER_TASK,          # 定时器任务
    SYSTEM_SCHED_ANNO,   # 系统调度注解
    SchedEventFlags,     # 事件调度标记
    SchedUpdateFlags,    # 更新调度标记
)

# SchedUpdateFlags
SchedUpdateFlags.BeforeUpdate  # 更新前
SchedUpdateFlags.Update         # 更新中
SchedUpdateFlags.AfterUpdate    # 更新后

# SchedEventFlags
SchedEventFlags.OnEvent         # 事件触发时