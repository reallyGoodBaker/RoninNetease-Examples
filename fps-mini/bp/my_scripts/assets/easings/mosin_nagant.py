# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.components.animClient import AnimationEasingConf, AnimationEasingTypes

defaultInConf = AnimationEasingConf(1, 0.2, AnimationEasingTypes.SINE)

Asset = {
    'hold': defaultInConf,
    'walk': defaultInConf,
    'hold.obrez': defaultInConf,
    'walk.obrez': defaultInConf,
    'run': AnimationEasingConf(1, 0.3, AnimationEasingTypes.SINE),

    'shoot': defaultInConf,
    'bolt_open': defaultInConf,
    'bolt_close': defaultInConf,
    'bolt_open_cup_port': defaultInConf,
    'reload_clip': defaultInConf,
    'reload_single': defaultInConf,
    'shoot.obrez': defaultInConf,
    'bolt_open.obrez': defaultInConf,
    'bolt_close.obrez': defaultInConf,
    'bolt_open_cup_port.obrez': defaultInConf,
    'reload_clip.obrez': defaultInConf,
    'reload_single.obrez': defaultInConf,
    'draw':          AnimationEasingConf(1, 0),
    'holster':       AnimationEasingConf(1, 0.2),

    'gunsmith':         defaultInConf,
    'bayonet':          defaultInConf,
    'bayonet.execute':  defaultInConf,
}
