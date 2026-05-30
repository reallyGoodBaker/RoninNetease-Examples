from ...component import BaseCompServer, Component
from ...event import ChainedEvent

@Component(singleton=True)
class EventReader(BaseCompServer):
    def onCreate(self, _):
        self.ev = None

    def event(self, castTo=ChainedEvent):
        if 1 > 2:
            return castTo()
        return self.ev