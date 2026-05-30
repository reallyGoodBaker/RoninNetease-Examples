from ..architect.plugins.animation.utils import BaseActionDispatcher, Dispatch
from ..architect.plugins.animation.components.animClient import AnimationExComponent
from ..architect.compact import *
from ..architect.math.utils import boxOverlap3dForward

@Dispatch('animation.standard_steve.attack.diamond')
class DiamondAttackDispatcher(BaseActionDispatcher):
    def onEnded(self, entityId, animComp):
        animComp.play('diamond', 'holding')

    def notifyAttackStart(self, entityId, animEx):
        # type: (str, AnimationExComponent) -> None
        entities = boxOverlap3dForward(entityId, (10, 10, 10), True)
        if len(entities):
            animInfo = animEx.getPlayingAnimation('attack')
            animInfo.playRate = 0.001
            def restore(*args):
                animInfo.playRate = 1
            TimerAdapter(0.2, restore).start()
            remote.client.call(
                'AnimPlayerServer.cameraShake'
            )
            remote.client.call(
                'AnimPlayerServer.doAttack',
                entities, 10
            )