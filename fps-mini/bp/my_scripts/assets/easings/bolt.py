# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.2, AnimationEasingTypes.SINE)

Asset = {
    'fp.hold': defaultInConf,
    'fp.run': AnimationEasingConf(1, 0.1),
    'fp.aim': defaultInConf,

    'fp.shoot': defaultInConf,
    'fp.reload_clip': defaultInConf,
    'fp.aim_shoot': defaultInConf,
    'fp.bolt_open': defaultInConf,
    'fp.bolt_close': AnimationEasingConf(1, 0.1),
    'fp.bolt_open_aim': defaultInConf,
    'fp.bolt_close_aim': AnimationEasingConf(1, 0.1),
    'fp.reload_single': defaultInConf,
}
