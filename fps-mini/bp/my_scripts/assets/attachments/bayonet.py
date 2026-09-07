from ...lib.stats import stats

Asset = {
    'attachmentId': 'ww1.bayonet',
    'category': 'bayonet',
    'texture': 'textures/attachments/bayonet',
    'bindItem': '',
    'displayName': 'slot.bayonet.name',
    'modifiers': [
        { 'stat': stats.adsIn,  'operation': '*', 'value': 1.4 },
        { 'stat': stats.adsOut, 'operation': '*', 'value': 1.4 },
    ],
    '+features': [
        {
            'name': 'bayonet',
            'params': {
                'animation': 'bayonet',
                'executeAnimation': 'bayonet.execute',
                'damage': 50
            }
        },
    ]
}