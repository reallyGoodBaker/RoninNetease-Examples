# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.1, AnimationEasingTypes.SINE)

Asset = {
    'fp.hold':          AnimationEasingConf(1, 0.2),
    'fp.run':           AnimationEasingConf(1, 0.3, AnimationEasingTypes.SINE),
    'fp.shoot':         defaultInConf,
    'fp.aim':           defaultInConf,
    'fp.aim_shoot':     defaultInConf,
    'fp.reload':        defaultInConf,
    'fp.slideopen':     AnimationEasingConf(1, 0.02),
    'fp.slideclose':     AnimationEasingConf(1, 0.05),
}
