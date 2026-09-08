from ...lib.stats import stats

Asset = {
    'attachmentId': 'ww1.telescope10x',
    'category': 'telescope',
    'texture': 'textures/attachments/scope2',
    'displayName': 'slot.telescope10x.name',
    'modifiers': [
        { 'stat': stats.adsIn, 'operation': '*', 'value': 1.4 },
        { 'stat': stats.modelScale, 'operation': '=', 'value': 0.3 },
        { 'stat': stats.fovScale, 'operation': '=', 'value': 2.5 },
        {
            'stat': stats.scopeEffect,
            'operation': '=',
            'value': {
                'scale': 4,         # 瞄准镜放大倍率
                'vignette': 0.359,      # 暗角
                'chroma': 0.245,         # 色散
                'bend': 0.329           # 边缘弯折
            }
        }
    ]
}