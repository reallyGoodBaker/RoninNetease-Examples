# -*- coding: utf-8 -*-
from ...engine.architect.utils.persona.client import RenderResources


Asset = {
    RenderResources.Geometries: {
        'weapon': 'geometry.weapons.auto',
    },
    RenderResources.Materials: {
        'weapon': 'netease_entity_alphatest_metallic',
        'glow': 'entity_emissive_alpha',
        'scope': 'entity_alphablend',
    },
    RenderResources.Textures: {
        'weapon': 'textures/entity/weapons/auto',
    },
    RenderResources.Animations: {
        'root_rot': 'animation.template.weapons.fp.rot'
    },
    RenderResources.RenderControllers: [
        'controller.render.template.weapon',
        'controller.render.template.arm',
    ],
}
