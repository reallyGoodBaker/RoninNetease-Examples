# -*- coding: utf-8 -*-

# ============================================
# 武器配置模板
# 武器 = 核心组件 + slots（配件槽位）
# ============================================

Asset = {
    # 枪机组件 - 决定射击循环与后坐力来源
    'bolt': {
        'cycleMode': 'auto',        # 循环模式: 'manual'(手动,如栓动) / 'auto'(自动回正,半自动/全自动)
        # 手动循环模式相关：
        'manualCycleTime': 2.0,     # 手拉枪机耗时(秒)
        'manualCycleAnim': '',      # 手拉枪机动画
        # 自动循环模式相关：
        'autoCycleOpenTime': 0.2,   # 击发后枪机完全打开的时间
        'autoCycleCloseTime': 0.2,  # 枪机从完全打开回到关闭的时间
        'cycleOpenAnim': '',        # 击发后枪机完全打开的时间
        'cycleCloseAnim': '',       # 枪机从完全打开回到关闭的时间
        # 通用属性：
        'holdOpenOnEmpty': True,        # 弹匣打空后是否挂起枪机(空仓挂机)
        'boltReleaseOnReload': False,   # 换弹后是否自动释放空挂 (部分武器换弹即释放)
        # 枪机后座撞击产生的后坐力冲量
        'recoil': [
            0.3,                    # 水平方向随机范围 [-x, x]
            0.8                     # 垂直方向基础值 [0, y]
        ],
        'emptyFireSound': '',       # 空仓射击音效，空字符串为不播放
    },

    # 扳机组件 - 决定开火模式与扳机逻辑
    'trigger': {
        'fireMode': 'auto',         # 支持的射击模式列表: 'auto', 'burst', 'boltAction'
        'isFullAuto': True,
        'burstCount': 3,            # 连发数量, 仅当 fireMode 为 'burst' 时生效
        'delay': 0.1                # 扳机延迟, 如果支持 burst, 子弹将会在这个时间段内以相同间隔发射 (棘轮)
    },

    # 供弹组件 - 决定弹药容纳方式与换弹流程
    'feed': {
        'magazineCapacity': 30,                     # 供弹具容量 (int)
        'ammoType': [ 'bullets.baseTemplate' ],     # 兼容的弹药Asset列表
        'reloadModes': [
            {
                'condition': 'empty',           # 在子弹完全空了的时候换弹
                'reloadType': 'replace',        # 将子弹数替换到 magazineCapacity
                'reloadTime': 2.5,              # 完全换弹耗时(空仓或战术换弹), replace时为主要耗时
                'tacticalReloadTime': 2.0,      # 膛内有弹时的换弹耗时(仅replace)
            },
            {
                'condition': 'clip_available',  # 在子弹可以分多漏夹装弹时
                'countPerClip': 5,              # 每个漏夹装填的数量
                'reloadType': 'add_clip',       # 将子弹数按每次 countPerClip 的数量分多次添加
                'reloadTime': 1.5,
            },
            {
                'condition': 'not_full',        # 在子弹没有填满的时候
                'reloadType': 'add',            # 添加一发, 比如霰弹枪
                'reloadTime': 0.4,
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
    'features': [
        'aiming',       # 基础瞄准功能
        'movement',     # 基础移动功能 (包含跳跃, 疾跑)
    ],

    # --- 配件槽位数组 (slots) ---
    # 所有可安装附件的槽位, 完全由数据定义
    'slots': [
        {
            'type': 'muzzle',                # 槽位类型, 自由字符串, 用于匹配附件
            'attachTo': 'muzzle_01',         # 绑定的骨骼名称
            'offset': (0, 0, 0),             # 绑骨的偏移
            'rotation': (0, 0, 0),           # 绑骨的旋转
            'scale': 1.0                     # 绑骨的缩放
        },
        {
            'type': 'optic',
            'attachTo': 'optic_01',
        },
        {
            'type': 'magazine',
            'attachTo': 'mag_01',
        },
        {
            'type': 'underbarrel',
            'attachTo': 'underbarrel_01',
        }
    ]
}