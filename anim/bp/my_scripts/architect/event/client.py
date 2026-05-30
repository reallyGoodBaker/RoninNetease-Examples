from .core import EventChain


class ClientEvents:
    globalEvents = {} # type: dict[tuple[str, bool], EventChain]

    @staticmethod
    def getOrCreateChain(eventType, isCustomEvent=False):
        # type: (str, bool) -> EventChain
        if (eventType, isCustomEvent) in ClientEvents.globalEvents:
            return ClientEvents.globalEvents[(eventType, isCustomEvent)]
        else:
            chain = EventChain(eventType)
            ClientEvents.globalEvents[(eventType, isCustomEvent)] = chain
            from ..core.subsystem import SubsystemManager
            SubsystemManager.getInstance().addListener(eventType, lambda ev: chain.dispatch(ev), isCustomEvent) # type: ignore
            return chain


def event(eventType, isCustomEvent=False):
    return ClientEvents.getOrCreateChain(eventType, isCustomEvent)