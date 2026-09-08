from ...lib.stats import stats

Asset = {
    'attachmentId': 'ww1.telescope3x',
    'category': 'telescope',
    'texture': 'textures/attachments/scope1',
    'displayName': 'slot.telescope3x.name',
    'modifiers': [
        { 'stat': stats.adsIn, 'operation': '*', 'value': 1.2 },
        { 'stat': stats.modelScale, 'operation': '=', 'value': 0.3 },
        { 'stat': stats.fovScale, 'operation': '=', 'value': 1 },
        {
            'stat': stats.scopeEffect,
            'operation': '=',
            'value': {
                'scale': 3,         # 瞄准镜放大倍率
                'vignette': 0.359,      # 暗角
                'chroma': 0.245,         # 色散
                'bend': 0.329           # 边缘弯折
            }
        }
    ]
}