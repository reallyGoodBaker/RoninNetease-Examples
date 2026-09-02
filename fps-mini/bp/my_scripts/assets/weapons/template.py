# -*- coding: utf-8 -*-

# ============================================
# 武器配置模板
# 武器 = 核心组件 + slots（配件槽位）
# ============================================

Asset = {
    # 枪机组件 - 决定射击循环与后坐力来源
    'bolt': {
        'cycleMode': 'auto',        # 循环模式: 'manual'(手动,如栓动和泵动) / 'auto'(自动回正,半自动/全自动)
        'boltOpenTime': 0.2,        # 击发后枪机完全打开的时间
        'boltCloseTime': 0.2,       # 枪机从完全打开回到关闭的时间
        # 全自动 / 半自动
        'disconnector': 'switch',   # 单发杆状态: 'none' 只允许连发, 'enable' 只允许单发, 'switch' 允许动态切换连发单发状态, 这个属性对手动枪机无效
        'holdOpenOnEmpty': True,    # 弹匣打空后是否挂起枪机 (空仓挂机, 仅对自动枪机有效)
        # 手动循环模式相关：
        'shootRestoreTime': 0.3,    # 射击后到可以手拉枪机的时间
        'cuppedPortOpenBolt': '',   # 当膛内有实弹拉开枪机（退膛）时播放的动画
        'cuppedPortOpenTime': 0,    # 当膛内有实弹拉开枪机（退膛）需要的时间
        # 枪机打开/关闭动画
        'boltOpenAnim': '',         # 枪机打开的动画, 当 cyclemode 为 manual 时会影响换弹动画
        'boltCloseAnim': '',        # 枪机关闭的动画, 当 cyclemode 为 manual 时会影响换弹动画
        # 枪机后座
        'recoil': {
            'value': [0.3, 0.5],    # 每次射击叠加的后坐力 (水平, 竖直)
            'decay': [0.2, 0.3],    # 每刻恢复的后坐力 (水平, 竖直)
        },
        # 枪机散布
        'spread': {
            'fnType': 'OneMinus',   # 枪机散步的函数类型，'OneMinus' 是 1 - f(x), 'Native' 是 f(x), 普通枪械使用 'OneMinus', 机枪使用 ‘Native’
            'strength': 0.3,        # 枪机散布的强度 (这是非线性的，建议多调试)
            'decay': 2,             # 每刻枪机恢复强度，值越大恢复越快 (大于1)
            'maxSpread': 1.5,
            'minSpread': 0.2,
        },
        'fireSound': '',            # 射击音效，空字符串为不播放
        'emptyFireSound': '',       # 空仓射击音效，空字符串为不播放
        'ejectVelocity': (1, 2, 0), # 退弹时给子弹附加的速度
    },

    # 扳机组件 - 决定开火模式与扳机逻辑
    'trigger': {
        'safe': False,              # 扳机保险, 为 False 时无法击发
        'fireMode': 'usual',        # 支持的射击模式列表: 'usual', 'burst'
        'burstCount': 3,            # 连发数量, 仅当 fireMode 为 'burst' 时生效
        'delay': 0.1                # 扳机延迟, 如果支持 burst, 子弹将会在这个时间段内以相同间隔发射 (棘轮)
    },

    # 供弹组件 - 决定弹药容纳方式与换弹流程
    'feed': {
        'canInterrupt': True,                       # 换弹是否可被打断
        'magazineCapacity': 30,                     # 供弹具容量 (int)
        'ammoType': [ 'bullets.baseTemplate' ],     # 兼容的弹药Asset列表
        'reloadModes': [
            {
                'condition': 'empty',           # 在子弹完全空了的时候换弹
                'reloadType': 'replace',        # 将子弹数替换到 magazineCapacity
                'reloadTime': 2.5,              # 完全换弹耗时(空仓或战术换弹), replace时为主要耗时
                'animation': '',                # 换弹动画
            },
            {
                'condition': 'clip_available',  # 在子弹可以分多漏夹装弹时
                'countPerClip': 5,              # 每个漏夹装填的数量
                'reloadType': 'add_clip',       # 将子弹数按每次 countPerClip 的数量分多次添加
                'reloadTime': 1.5,
                'animation': '',
            },
            {
                'condition': 'not_full',        # 在子弹没有填满的时候
                'reloadType': 'add',            # 添加一发, 比如霰弹枪
                'reloadTime': 0.4,
                'animation': '',
            },
        ]
    },

    # 枪管组件 - 决定子弹初速和子弹散步
    'barrel': {
        'velocityModifier': 1.0,        # 子弹的 baseSpeed 乘以这个值就是出膛速度
        'maxSpread': 1.0,               # 子弹的最大散布角度
        'spreadIncreasePerShot': 0.1,   # 每次射击增加的散布角度
    },

    # 操控性 - 影响玩家操纵手感
    'handling': {
        'speedModifier': 1.0,       # 移动速度倍率
        'canJump': True,
        'canSprint': True,
        'adsInTime': 0.25,          # 进入开镜的时间
        'adsOutTime': 0.25,         # 退出开镜的时间
        'sprintToFireTime': 0.2,    # 跑射延迟
    },

    # 更多 - 可以自定义处理
    'extra': {
        'slide': {                  # 滑铲射击配置, 这部分数据完全暴露，需要时直接获取
            'canSlideShoot': True,
            'slideToFireTime': 0.35,
            'slideToADS_Time': 0.45,
        }
    },

    # 功能 - 定义玩家控制项 (里面的功能由代码驱动)
    'features': {
        'shoot': {
            'animation': ''
        },
        'aim': {     # 基础瞄准功能
            'scale': 1.2,
            'camera': 'iron_sight',     # 瞄准时相机名称
            'modelScale': 1,            # 瞄准时z轴缩放
            'ads': 0.5,                 # 瞄准需要的时间
            'scope_effect': None        # 倍镜效果（这部分示例在sniper.py）
        },
        'movement': {   # 基础移动功能
            'walkAnim': '',
            'sprintAnim': '',
            'draw': 'fp.draw',
            'holster': 'fp.holster',
            'spread': 1,
        },
    },

    # --- 配件槽位数组 (slots) ---
    # 所有可安装附件的槽位, 完全由数据定义
    'slots': [
        {
            'category': 'muzzle',                # 槽位类型, 自由字符串, 用于匹配附件
            'attachTo': 'muzzle_01',         # 绑定的骨骼名称
            'offset': (0, 0, 0),             # 绑骨的偏移
            'rotation': (0, 0, 0),           # 绑骨的旋转
            'scale': 1.0                     # 绑骨的缩放
        },
        {
            'category': 'optic',
            'attachTo': 'optic_01',
        },
        {
            'category': 'magazine',
            'attachTo': 'mag_01',
        },
        {
            'category': 'underbarrel',
            'attachTo': 'underbarrel_01',
        }
    ]
}