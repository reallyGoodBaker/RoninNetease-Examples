from ...core.unreliable import Unreliable
from ...component import getOneComponent, NeC
from .enum import AnimExEvents

class AnimationEventDispatcher(Unreliable):
    dispatchers = {}
    animDispatcherMapping = {}

    @classmethod
    def getOrCreate(cls, animName):
        clsName = cls.__name__
        dispatcher = AnimationEventDispatcher.getDispatcher(animName)
        if dispatcher is None:
            if clsName not in AnimationEventDispatcher.dispatchers:
                dispatcher = cls()
                AnimationEventDispatcher.dispatchers[clsName] = dispatcher
            if animName not in AnimationEventDispatcher.animDispatcherMapping:
                AnimationEventDispatcher.animDispatcherMapping[animName] = clsName
        return dispatcher
    
    @staticmethod
    def getDispatcher(animName):
        return AnimationEventDispatcher.dispatchers.get(
            AnimationEventDispatcher.animDispatcherMapping.get(animName, None)
        )

    def _callNamedMethod(self, methodName, *args):
        method = getattr(self, methodName, None)
        if callable(method):
            self.tryCall(method, *args)

    def dispatch(self, ev, animComp):
        entityId = ev['entityId']
        typeStr = ev['type']
        if typeStr == AnimExEvents.Interrupted:
            self._callNamedMethod('onInterrupted', entityId, animComp)
            return self._callNamedMethod('onEnded', entityId, animComp)
        elif typeStr == AnimExEvents.Finish:
            self._callNamedMethod('onFinish', entityId, animComp)
            return self._callNamedMethod('onEnded', entityId, animComp)
        elif typeStr == AnimExEvents.Notify:
            state = 'Start' if ev['state'] else 'End'
            notifyName = ev['notifyName'] # type: str
            capitalizedName = ''.join(map(lambda s: s.capitalize(), notifyName.split('_')))
            methodName = 'notify' + capitalizedName + state.capitalize()
            return self._callNamedMethod(methodName, entityId, animComp)

    def onEnded(self, entityId, animComp):
        """
        动画被打断或者正常结束时都会调用
        """
        pass

    def onInterrupted(self, entityId, animComp):
        """
        动画被打断时调用
        """
        pass

    def onFinish(self, entityId, animComp):
        """
        动画正常结束时调用
        """
        pass


def Dispatch(animName):
    def wrapper(cls):
        cls.getOrCreate(animName)
        return cls
    return wrapper


# TODO: should ignore
# from mod.client.component.cameraCompClient import CameraComponentClient
# from mod.client.component.operationCompClient import OperationCompClient


class BaseActionDispatcher(AnimationEventDispatcher):
    """
    预定义了 v.notify_stun, v.notify_camlock
    """
    def movement(self, entityId, canMove=True):
        op = getOneComponent(entityId, NeC.Operation)
        op.SetCanMove(canMove)
        op.SetCanJump(canMove)

    def cam(self, entityId, lock=False):
        op = getOneComponent(entityId, NeC.Operation)
        op.SetCanDrag(not lock)

    def notifyStunStart(self, entityId, animEx):
        self.movement(entityId, False)

    def notifyStunEnd(self, entityId, animEx):
        self.movement(entityId, True)

    def onInterrupted(self, entityId, animEx):
        self.movement(entityId, True)

    def onFinish(self, entityId, animEx):
        self.movement(entityId, True)