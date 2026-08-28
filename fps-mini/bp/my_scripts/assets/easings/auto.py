# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.15, AnimationEasingTypes.SINE)

Asset = {
    'fp.hold':          AnimationEasingConf(1, 0.2),
    'fp.run':           AnimationEasingConf(1, 0.3, AnimationEasingTypes.SINE),
    'fp.shoot':         defaultInConf,
    'fp.reload':        defaultInConf,
    'fp.reload_empty':  defaultInConf,
    'fp.slideopen':     defaultInConf,
    'fp.slideclose':    defaultInConf,
}
