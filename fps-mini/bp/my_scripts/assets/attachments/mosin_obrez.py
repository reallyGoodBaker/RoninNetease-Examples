from ...lib.stats import stats

Asset = {
    'attachmentId': 'ww1.mosin_obrez',
    'category': 'mosin_obrez',
    'texture': 'textures/attachments/mosin_obrez',
    'displayName': 'slot.obrez.name',
    'value': 1,
    'modifiers': [
        { 'stat': stats.adsIn,              'operation': '*', 'value': 0.5 },
        { 'stat': stats.adsOut,             'operation': '*', 'value': 0.5 },
        { 'stat': stats.modelScale,         'operation': '=', 'value': 0.6 },
        { 'stat': stats.spreadMultiplier,   'operation': '=', 'value': 0.5 },
        { 'stat': stats.shootRestoreTime,   'operation': '=', 'value': 0.4 },
        { 'stat': stats.cuppedPortOpenTime, 'operation': '=', 'value': 0.94 },
        { 'stat': stats.boltOpenTime,       'operation': '=', 'value': 0.48 },
        { 'stat': stats.boltCloseTime,      'operation': '=', 'value': 0.54 },
        { 'stat': stats.animCuppedPort,     'operation': '=', 'value': 'bolt_open_cup_port.obrez' },
        { 'stat': stats.animShoot,          'operation': '=', 'value': 'shoot.obrez' },
        { 'stat': stats.animBoltOpen,       'operation': '=', 'value': 'bolt_open.obrez' },
        { 'stat': stats.animBoltClose,      'operation': '=', 'value': 'bolt_close.obrez' },
        { 'stat': stats.animWalk,           'operation': '=', 'value': 'walk.obrez' },
        { 'stat': stats.animHold,           'operation': '=', 'value': 'hold.obrez' },
        { 'stat': stats.velocityModifier,   'operation': '=', 'value': 0.8 },
        {
            'stat': stats.spread,
            'operation': '=',
            'value': {
                'fnType': 'OneMinus',
                'strength': 0.3,
                'decay': 2,
                'maxSpread': 4,
                'minSpread': 0.8,
            },
        },
        {
            'stat': stats.reloadModes,
            'operation': '=',
            'value': [
                {
                    'condition': 'clip_available',  # 在子弹可以分多漏夹装弹时
                    'countPerClip': 5,              # 每个漏夹装填的数量
                    'reloadType': 'add_clip',       # 将子弹数按每次 countPerClip 的数量分多次添加
                    'reloadTime': 1.67,
                    'animation': 'reload_clip.obrez',
                },
                {
                    'condition': 'not_full',        # 在子弹没有填满的时候
                    'reloadType': 'add',            # 添加一发, 比如霰弹枪
                    'reloadTime': 0.75,
                    'animation': 'reload_single.obrez',
                },
            ]
        }
    ]
}