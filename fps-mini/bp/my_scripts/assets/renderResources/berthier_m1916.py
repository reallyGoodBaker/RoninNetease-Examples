Asset = {
    'model': 'geometry.ww1.berthier_m1916',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.berthier_m1916',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/berthier_m1916',
    'metalTexture': 'textures/entity/weapons/berthier_m1916_metal',
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
        'reload_clip': 'berthier_m1916.reload_clip',
        'bolt_open': 'berthier_m1916.bolt_open',
        'bolt_close': 'berthier_m1916.bolt_close',
        'drop_clip': 'berthier_m1916.drop_clip',
    }
}