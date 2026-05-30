import time

from ...core.scheduler import TimerAdapter


def throttle(func, wait):
    func.last = 0
    def wrapper():
        now = time.time()
        if now - func.last >= wait:
            func.last = now
            return func()
    return wrapper


def debounce(func, wait):
    func.timer = None
    def wrapper():
        if func.timer:
            func.timer.cancel()
        func.timer = TimerAdapter(wait, func)
        func.timer.start()
    return wrapper


def memoize(func):
    memoize.cache = {}
    def wrapper(*args, **kwargs):
        key = (args, tuple(sorted(kwargs.items())))
        if key not in memoize.cache:
            memoize.cache[key] = func(*args, **kwargs)
        return memoize.cache[key]
    return wrapper


def compVer(ver1, ver2):
    # type: (list[int], list[int]) -> int
    for a, b in map(None, ver1, ver2):
        if a < b: return -1
        if a > b: return 1
    return 0