Asset = {
    'model': 'geometry.ww1.ross_mk3',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.ross_mk3',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/ross_mk3',
    'metalTexture': 'textures/entity/weapons/ross_mk3_metal',
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
        'reload_clip': 'ross_mk3.reload_clip',
        'bolt_open': 'ross_mk3.bolt_open',
        'bolt_close': 'ross_mk3.bolt_close',
        'reload_single': 'ross_mk3.reload_single',
    }
}