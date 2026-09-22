# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.2, AnimationEasingTypes.SINE)

Asset = {
    'hold': defaultInConf,
    'walk': defaultInConf,
    'run': AnimationEasingConf(1, 0.3, AnimationEasingTypes.SINE),
    'aim': defaultInConf,

    'shoot': defaultInConf,
    'reload': defaultInConf,
    'aim_shoot': defaultInConf,
    'bolt_open': defaultInConf,
    'bolt_close': defaultInConf,
    'bolt_open_aim': defaultInConf,
    'bolt_open_cup_port': defaultInConf,
    'bolt_close_aim': AnimationEasingConf(1, 0),
    'draw':          AnimationEasingConf(1, 0),
    'holster':       AnimationEasingConf(1, 0.2),

    'gunsmith':         defaultInConf,
    'bayonet':          defaultInConf,
    'bayonet.execute':  defaultInConf,
}
