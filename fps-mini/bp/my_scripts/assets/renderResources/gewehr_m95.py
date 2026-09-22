Asset = {
    'model': 'geometry.ww1.gewehr_m95',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.gewehr_m95',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/gewehr_m95',
    'metalTexture': 'textures/entity/weapons/gewehr_m95_mert',
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
        'bolt_open': 'gewehr_m95.bolt_open',
        'bolt_close': 'gewehr_m95.bolt_close',
        'loaded': 'gewehr_m95.loaded',
        'drop_clip': 'gewehr_m95.drop_clip',
        'shoot': 'gewehr_m95.shoot',
    }
}