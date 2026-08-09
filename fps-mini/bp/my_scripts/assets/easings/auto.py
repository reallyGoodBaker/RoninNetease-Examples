# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.15)

Asset = {
    'fp.hold':          AnimationEasingConf(1, 0.2),
    'fp.run':           defaultInConf,
    'fp.shoot':         defaultInConf,
    'fp.aim':           AnimationEasingConf(1, 0.1),
    'fp.aim_shoot':     defaultInConf,
    'fp.reload':        defaultInConf,
    'fp.reload_empty':        defaultInConf,
}
