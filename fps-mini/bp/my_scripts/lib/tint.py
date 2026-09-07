# -*- coding: utf-8 -*-
"""Shared weapon tint Molang variables.

Appearance is applied through the same server-state path as attachments:
whenever the server returns a gun state, the client writes the appearance
colors to these QueryVariables.
"""
from ..engine.architect.compact import QueryVariable, localPlayerId


tintColorR = QueryVariable('tint_color_r', 1)
tintColorG = QueryVariable('tint_color_g', 1)
tintColorB = QueryVariable('tint_color_b', 1)
tintColorA = QueryVariable('tint_color_a', 0)

# Default overlay strength when an appearance has no explicit alpha.
_DEFAULT_ALPHA = 0.6


def applyAppearance(appearance):
    # type: (dict | None) -> None
    rgb = None
    alpha = _DEFAULT_ALPHA
    if isinstance(appearance, dict):
        candidate = appearance.get('rgb')
        if isinstance(candidate, (list, tuple)) and len(candidate) >= 3:
            rgb = candidate
        if 'alpha' in appearance:
            alpha = float(appearance.get('alpha', _DEFAULT_ALPHA))
    if rgb is None:
        clearAppearance()
        return
    print '[Tint] applyAppearance rgb=', rgb, 'alpha=', alpha
    tintColorR.setValue(localPlayerId(), float(rgb[0]) / 255.0)
    tintColorG.setValue(localPlayerId(), float(rgb[1]) / 255.0)
    tintColorB.setValue(localPlayerId(), float(rgb[2]) / 255.0)
    tintColorA.setValue(localPlayerId(), alpha)


def clearAppearance():
    # type: () -> None
    tintColorR.setValue(localPlayerId(), 1.0)
    tintColorG.setValue(localPlayerId(), 1.0)
    tintColorB.setValue(localPlayerId(), 1.0)
    tintColorA.setValue(localPlayerId(), 0.0)
