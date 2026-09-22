from ...lib.stats import stats

Asset = {
    'attachmentId': 'attachement.smle_mk3_quick_shoot',
    'category': 'smle_mk3_skill',
    'displayName': 'attachment.smle_mk3_quick_shoot.name',
    'texture': 'textures/attachments/quick_shoot',
    'modifiers': [
        { 'stat': stats.shootRestoreTime, 'operation': '=', 'value': 0.1 },
        { 'stat': stats.boltOpenTime, 'operation': '=', 'value': 0.3 },
        { 'stat': stats.boltCloseTime, 'operation': '=', 'value': 0.2 },
        {
            'stat': stats.spread,
            'operation': '=',
            'value': {
                'fnType': 'OneMinus',
                'strength': 1,
                'decay': 1.1,
                'maxSpread': 3,
                'minSpread': 1,
            }
        },
    ]
}