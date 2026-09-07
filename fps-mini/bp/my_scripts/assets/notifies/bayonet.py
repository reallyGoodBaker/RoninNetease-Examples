# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.utils import BaseActionDispatcher, Dispatch
from ...engine.architect.compact import (
    remote, getOneSingletonComponent,
)
from ...engine.architect.math.utils import boxOverlap3dForward
from ...lib.feature import LocalFeaturesComponent

@Dispatch('animation.weapons.bolt.bayonet.execute')
class BayonetExecuteDispatcher(BaseActionDispatcher):
    def notifyAttckStart(self, entity, animEx):
        hurts = boxOverlap3dForward(entity, (4, 4, 5), True)
        if len(hurts) == 0:
            return

        target = hurts[0]
        features = getOneSingletonComponent(LocalFeaturesComponent)
        if not features.hasFeature('bayonet'):
            return
        damage = features.getFeature('bayonet').params['damage']
        remote.client.call(
            'BulletServerAuthSystem.tryDamageEntity',
            target, damage, False, 'bayonet'
        )
