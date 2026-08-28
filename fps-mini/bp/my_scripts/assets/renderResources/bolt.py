Asset = {
    'model': 'geometry.weapons.bolt',
    'arms': 'geometry.arms.bolt',
    'materials': {
        'weapon': 'metallic_without_smooth',
        'glow': 'entity_emissive_alpha',
        'scope': 'scope',
        'eyepiece': 'eyepiece',
    },
    'texture': 'textures/entity/weapons/bolt',
    'render': {
        'first_person': [
            'controller.render.template.weapon',
            'controller.render.fps.arm'
        ],
        'third_person': []
    }
}