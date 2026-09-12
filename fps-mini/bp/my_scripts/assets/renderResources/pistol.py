Asset = {
    'model': 'geometry.template.pistol',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.pistol',
    'materials': {
        'weapon': 'pbr_tint',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/pistol',
    'metalTexture': 'textures/entity/weapons/pistol_metal',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.first_person.arm'
        ],
        'third_person': []
    }
}