Asset = {
    'model': 'geometry.template.pistol',
    'arms': 'geometry.arms.pistol',
    'materials': {
        'weapon': 'metallic_without_smooth',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/pistol',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.fps.arm'
        ],
        'third_person': []
    }
}