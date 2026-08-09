# -*- coding: utf-8 -*-
from ...engine.architect.utils.persona.client import RenderResources


Asset = {
    RenderResources.Geometries: {
        'weapon': 'geometry.template.pistol',
    },
    RenderResources.Materials: {
        'weapon': 'netease_entity_alphatest_metallic',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
    },
    RenderResources.Textures: {
        'weapon': 'textures/entity/weapons/pistol',
    },
    RenderResources.Animations: {
        'root_rot': 'animation.template.weapons.fp.rot'
    },
    RenderResources.RenderControllers: [
        { 'controller.render.template.weapon': 'v.is_first_person' },
        { 'controller.render.fps.arm': 'v.is_first_person' },
    ],
}
