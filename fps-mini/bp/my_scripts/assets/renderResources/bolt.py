Asset = {
    'model': 'geometry.weapons.bolt',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.bolt',
    'materials': {
        'weapon': 'metallic_without_smooth',
        'tint_overlay': 'entity_alphatest',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/bolt',
    'tintMaskTexture': 'textures/entity/weapons/bolt_tint_mask',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.tint.overlay',
            'controller.render.first_person.arm'
        ],
        'third_person': [
            'controller.render.third_person.torso',
            'controller.render.third_person.weapon',
            'controller.render.tint.overlay'
        ]
    }
}