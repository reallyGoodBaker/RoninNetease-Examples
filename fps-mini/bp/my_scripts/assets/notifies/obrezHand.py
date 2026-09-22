# -*- coding: utf-8 -*-
from ...engine.architect.plugins.animation.utils import BaseActionDispatcher, Dispatch
from ...engine.architect.compact import (
    NamedVariable
)

showObrezLeftHand = NamedVariable('show_lefthand')

@Dispatch('animation.ww1.mosin_nagant_m1891.hold')
@Dispatch('animation.ww1.mosin_nagant_m1891.hold_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.walk_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.shoot_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.bolt_open_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.bolt_close_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.reload_single_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.reload_clip_obrez')
@Dispatch('animation.ww1.mosin_nagant_m1891.bolt_open_cup_port_obrez')
class ObrezHandDispatcher(BaseActionDispatcher):
    def notifyHandStart(self, entity, animEx):
        showObrezLeftHand.setValue(entity, 1)

    def notifyHandEnd(self, entity, animEx):
        showObrezLeftHand.setValue(entity, 0)
