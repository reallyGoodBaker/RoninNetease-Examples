from ...engine.architect.utils.persona.client import RenderResources


Asset = {
    RenderResources.Geometries: {
        'weapon': 'geometry.weapons.bolt',
    },
    RenderResources.Materials: {
        'weapon': 'netease_entity_alphatest_metallic',
    },
    RenderResources.Textures: {
        'weapon': 'textures/entity/weapons/bolt',
    },
    RenderResources.Animations: {
        'root_rot': 'animation.template.weapons.pistol.fp.rot',
    },
    RenderResources.RenderControllers: [
        'controller.render.template.weapon',
        'controller.render.template.arm',
    ],
}