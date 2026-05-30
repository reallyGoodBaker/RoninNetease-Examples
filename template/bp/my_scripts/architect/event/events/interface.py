from ..core import Ref

class ChainedEvent(object):
    def stop(self):
        """停止事件传递"""
        pass

    def prevent(self):
        """阻止默认事件 (cancel 设置为 True)"""
        pass

    def dict(self):
        # type: () -> dict
        pass
    
    def setEvent(self, p, v):
        # type: (str, object) -> None
        pass

    def updateEvent(self, updates):
        # type: (dict) -> None
        pass

    def clone(self):
        # type: () -> ChainedEvent
        pass