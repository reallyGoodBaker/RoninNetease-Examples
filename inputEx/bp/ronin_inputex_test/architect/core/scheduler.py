# coding=utf-8
from .basic import compClient, compServer, isServer, clientApi, serverApi
from time import time
from types import FunctionType, GeneratorType
from functools import wraps
from .unreliable import Unreliable
from .annotation import AnnotationHelper
from ..conf import TIMER_TASK, SYSTEM_SCHED_ANNO, SchedEventFlags, SchedUpdateFlags


class Task:
    taskId = 0

    def __init__(self, fn):
        self.fn = fn  # type: FunctionType
        self.id = Task.taskId
        self.finished = False  # type: bool
        Task.taskId += 1


class SuspendableTask:
    def __init__(self, generator):
        self.fn = generator  # type: GeneratorType
        self.gen = generator()
        self.id = Task.taskId
        self.finished = False  # type: bool
        Task.taskId += 1

    def callOnce(self):
        if self.finished:
            return None

        try:
            return next(self.gen)
        except StopIteration:
            self.finished = True
            return None

class Scheduler:
    def __init__(self):
        self._sequenceExecuting = False
        self._lastExecutedTime = time()
        self._skippedUpdates = 0
        self._innerTicks = 0
        self._scheduleQueues = {}  # type: dict[str, list[Task]]
        self._executingThreads = []  # type: list[Task]
        self.scheduleSequence = (
            SchedUpdateFlags.BeforeUpdate,
            SchedUpdateFlags.Update,
            SchedUpdateFlags.AfterUpdate,
        )
        self._shouldRemoveTaskFns = []


    def _getTaskQueue(self, scheduleFlag):
        # type: (str) -> list
        queue = self._scheduleQueues.get(scheduleFlag)
        if queue is None:
            queue = []
            self._scheduleQueues[scheduleFlag] = queue

        return queue


    def execute(self, scheduleFlag, args=[]):
        queue = self._getTaskQueue(scheduleFlag)
        for t in queue:
            if t.fn in self._shouldRemoveTaskFns:
                queue.remove(t)
                self._shouldRemoveTaskFns.remove(t.fn)
                continue

            self._executingThreads.append(t)

        for t in self._executingThreads:
            if isinstance(t, Task):
                t.fn(*args)
                self._executingThreads.remove(t)

            elif isinstance(t, SuspendableTask):
                t.callOnce()
                if t.finished:
                    self._executingThreads.remove(t)


    def addTask(self, scheduleFlag, fn):
        # type: (str, FunctionType) -> int
        queue = self._getTaskQueue(scheduleFlag)
        task = Task(fn)
        queue.append(task)
        return task.id


    def addSuspendableTask(self, scheduleFlag, generator):
        # type: (str, GeneratorType) -> int
        queue = self._getTaskQueue(scheduleFlag)
        task = SuspendableTask(generator)
        queue.append(task)
        return task.id


    # 注意, 如果 taskId=-1, 则移除该 scheduleFlag 下的所有任务
    def removeTask(self, scheduleFlag, taskId=-1):
        # type: (str, int) -> None
        queue = self._getTaskQueue(scheduleFlag)
        if taskId != -1:
            for task in queue:
                if task.id == taskId:
                    queue.remove(task)
                    return
        else:
            queue.clear()


    def executeSequence(self, *args):
        """
        :rtype: tuple[float, int]
        :return: (deltaTime, skippedUpdates)
        """
        self._innerTicks += 1
        if self._sequenceExecuting:
            self._skippedUpdates += 1
            return 0.0, self._skippedUpdates

        self._sequenceExecuting = True
        self.execute(TIMER_TASK, args)
        for scheduleFlag in self.scheduleSequence:
            self.execute(scheduleFlag, args)

        dt = time() - self._lastExecutedTime
        self._lastExecutedTime = time()
        self._sequenceExecuting = False

        return dt, self._skippedUpdates


    def _timeoutWrapper(self, fn, ticks, once=False):
        startTick = self._innerTicks

        def wrapper():
            if (self._innerTicks - startTick) % ticks <= 0:
                fn()
                if once:
                    self._shouldRemoveTaskFns.append(wrapper)

        return wrapper


    def addPeriodicTask(self, fn, ticks=1, interval=False):
        return self.addTask(
            TIMER_TASK,
            self._timeoutWrapper(fn, max(1, ticks), not interval),
        )

    def runTimeout(self, fn, ticks=1):
        return self.addPeriodicTask(fn, ticks, False)
    
    def runInterval(self, fn, ticks=1):
        return self.addPeriodicTask(fn, ticks, True)

    def run(self, fn):
        return self.addPeriodicTask(fn)
    
    def clearTimeout(self, taskId):
        self.removeTask(TIMER_TASK, taskId)


def addTimer(period, fn):
    GameServer = compServer.CreateGame(serverApi.GetLevelId())
    GameClient = compClient.CreateGame(clientApi.GetLevelId())
    game = GameServer if isServer() else GameClient
    return game.AddRepeatedTimer(period, fn)

def cancelTimer(timer):
    GameServer = compServer.CreateGame(serverApi.GetLevelId())
    GameClient = compClient.CreateGame(clientApi.GetLevelId())
    game = GameServer if isServer() else GameClient
    game.CancelTimer(timer)


class TimerAdapter(object):
    def __init__(self, period, fn):
        self.period = period
        self.fn = fn
        self.timer = None
    
    def start(self):
        self.timer = addTimer(self.period, self.fn)

    def cancel(self):
        if self.timer:
            cancelTimer(self.timer)
            self.timer = None


class SchedulerPoller(Unreliable):
    def __init__(self, scheduler, period=1):
        # type: (Scheduler, float) -> None
        Unreliable.__init__(self)
        self.period = period
        self.scheduler = scheduler
        self.timer = TimerAdapter(self.period, lambda: self.tryCall(scheduler.executeSequence))

    def start(self):
        self.timer.start()

    def cancel(self):
        self.timer.cancel()


class SimpleFixedScheduler(SchedulerPoller):
    def __init__(self, period=1):
        SchedulerPoller.__init__(self, Scheduler(), period)


class Sched:
    TYPE_TICK = 1
    TYPE_RENDER = 2
    TYPE_FIXED = 3
    TYPE_EVENT = 4

    @staticmethod
    def Tick(scheduleFlag=SchedUpdateFlags.Update):
        # type: (str) -> FunctionType
        def wrapper(fn):
            AnnotationHelper.addAnnotation(fn, SYSTEM_SCHED_ANNO, [Sched.TYPE_TICK, scheduleFlag, None])
            return fn
        return wrapper

    @staticmethod
    def Render(scheduleFlag=SchedUpdateFlags.Update):
        # type: (str) -> FunctionType
        def wrapper(fn):
            AnnotationHelper.addAnnotation(fn, SYSTEM_SCHED_ANNO, [Sched.TYPE_RENDER, scheduleFlag, None])
            return fn
        return wrapper
    
    @staticmethod
    def Fixed(schedulerName, scheduleFlag=TIMER_TASK):
        # type: (str, str) -> FunctionType
        def wrapper(fn):
            AnnotationHelper.addAnnotation(fn, SYSTEM_SCHED_ANNO, [Sched.TYPE_FIXED, scheduleFlag, {
                'schedulerName': schedulerName
            }])
            return fn
        return wrapper
    
    @staticmethod
    def Event(eventType, isCustom=False, scheduleFlag=SchedEventFlags.Event):
        # type: (str, bool, str) -> FunctionType
        def wrapper(fn):
            AnnotationHelper.addAnnotation(fn, SYSTEM_SCHED_ANNO, [Sched.TYPE_EVENT, scheduleFlag, {
                'isCustom': isCustom,
                'eventType': eventType
            }])
            return fn
        return wrapper


class Future(Unreliable):

    PENDING = 0
    FULFILLED = 1
    REJECTED = 2

    def __init__(self, executor):
        Unreliable.__init__(self)
        self.executor = executor
        self.result = tuple() # type: tuple
        self.status = Future.PENDING
        self._done = []
        self._expected = []
        self.tryCall(self.executor, self._resolve, self._reject)

    def _resolve(self, *value):
        self.result = value
        self.status = Future.FULFILLED
        for callback in self._done:
            self.tryCall(callback, *value)

    def _reject(self, *value):
        self.result = value
        self.status = Future.REJECTED
        for callback in self._expected:
            self.tryCall(callback, *value)

    def done(self, callback):
        if self.status == Future.FULFILLED:
            self.tryCall(callback, *self.result)
        elif self.status == Future.PENDING:
            self._done.append(callback)
        return self

    def expected(self, callback):
        if self.status == Future.REJECTED:
            self.tryCall(callback, *self.result)
        elif self.status == Future.PENDING:
            self._expected.append(callback)
        return self
    
    @staticmethod
    def resolvers():
        _resolvers = []
        def _executor(r, j):
            _resolvers.append(r)
            _resolvers.append(j)
        ftr = Future(_executor)
        res = _resolvers[0]
        rej = _resolvers[1]
        return ftr, res, rej
    

def Async(func):
    """
    装饰器：将生成器函数转换为返回 Future 的异步函数。
    调用时自动启动协程，yield 出的 Future 会被等待，
    协程的最终返回值作为 Future 的 resolve 值。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        ftr, resolve, reject = Future.resolvers()

        def advance(value=None, exc=None):
            """驱动生成器执行一步"""
            try:
                if exc is not None:
                    yielded = gen.throw(exc)
                else:
                    if value is None:
                        yielded = gen.next()
                    else:
                        yielded = gen.send(value)
            except StopIteration as e:
                # 生成器正常结束，e.value 在 Python 2.7 中需要特殊处理
                # StopIteration 没有 value 属性，需要从 args 中获取
                result = e.args[0] if e.args else None
                resolve(result)
                return
            except Exception as e:
                reject(e)
                return

            # 等待 yield 出来的 Future
            if isinstance(yielded, Future):
                # 注册成功回调
                yielded.done(lambda *res: advance(res[0] if res else None, None))
                # 注册失败回调
                yielded.expected(lambda *err: advance(None, err[0] if err else Exception("Future rejected")))
            else:
                reject(TypeError("Yielded object is not a Future: %s" % type(yielded)))

        # 启动协程
        advance()
        return ftr
    return wrapper