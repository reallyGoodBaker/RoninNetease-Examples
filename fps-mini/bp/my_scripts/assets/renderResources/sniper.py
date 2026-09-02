Asset = {
    'model': 'geometry.weapons.sniper',
    'third_model': 'geometry.template.third.bolt',
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
            'controller.render.first_person.arm'
        ],
        'third_person': []
    }
}