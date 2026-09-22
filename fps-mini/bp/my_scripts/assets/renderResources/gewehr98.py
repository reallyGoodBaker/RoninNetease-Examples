Asset = {
    'model': 'geometry.ww1.gewehr98',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.gewehr98',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/gewehr98',
    'metalTexture': 'textures/entity/weapons/gewehr98_metal',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.first_person.arm'
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