Asset = {
    'model': 'geometry.template.mp18',
    'third_model': 'geometry.template.third.bolt',
    'arms': 'geometry.arms.mp18',
    'materials': {
        'weapon': 'metallic_without_smooth',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/auto',
    'metalTexture': 'textures/entity/weapons/auto_metal',
    'render': {
        'first_person': [
            'controller.render.template.mp18',
            'controller.render.first_person.arm'
        ],
        'third_person': []
    }
}