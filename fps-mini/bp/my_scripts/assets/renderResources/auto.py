Asset = {
    'model': 'geometry.template.mp18',
    'arms': 'geometry.arms.mp18',
    'materials': {
        'weapon': 'metallic_without_smooth',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/auto',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.fps.arm'
        ],
        'third_person': []
    }
}