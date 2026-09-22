Asset = {
    'model': 'geometry.ww1.mosin_nagant_m1891',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.mosin_nagant_m1891',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/mosin_nagant_m1891',
    'metalTexture': 'textures/entity/weapons/mosin_nagant_m1891_mert',
    'render': {
        'first_person': [
            'controller.render.mosin_nagant',
            'controller.render.arm.mosin_nagant'
        ],
        'third_person': [
            'controller.render.third_person.torso',
            'controller.render.third_person.weapon'
        ]
    },
    'sounds': {
        'reload_clip': 'gew98.reload_clip',
        'bolt_open': 'gew98.bolt_open',
        'bolt_close': 'gew98.bolt_close',
        'reload_single': 'gew98.reload_single',
    }
}