# -*- coding: utf-8 -*-

# ============================================
# 子弹配置模板
# 子弹 = projectile (弹道核心) + payloads[] (弹头载荷数组)
# ============================================

Asset = {
    # 弹道
    'projectile': {
        'baseSpeed': 300,               # 初速基准值 (米/秒), 最终初速 = 此值 + 枪管加成
        'gravity': -2,                  # 重力值（为了娱乐性不采用真实的重力）
        'drag': 0.05,                   # 空气阻力系数, 影响速度衰减 (0为无衰减)
        'caliber': '9mm',               # 口径标识 (string), 作为 customTag 传入 hurt 组件
        'bounce': False,                # 子弹可弹跳（比如榴弹）
        'ignoreEntities': 'penetrate.entities',     # 子弹不处理的实体
    },

    # 子弹销毁条件
    'destroy': {
        'duration': 5,                  # 子弹最大存活时间
        'velocity': 0,                  # 子弹最小速度
        'distance': 1000,               # 子弹最远飞行距离
    },

    # 子弹穿透设置
    'penetrate': {
        'penetrateBlocks': 'penetrate.template',    # 可穿透方块数组 Asset
        'damageRetentionPerPass': 0.7,              # 每次穿透后伤害保留比例
        'velocityRetentionPerPass': 0.7,            # 每次穿透后速度保留比例
        'minPenetrateSpeed': 250,                   # 最小穿透速度
    },

    # --- 弹头载荷数组 (命中后按顺序激活的效果) ---
    # 每个载荷是一个独立模块, 可自由组合实现击中、燃烧、爆炸等
    'payloads': [
        # 载荷1: 动能伤害 (几乎必选)
        {
            'type': 'kinetic',                      # 载荷类型
            'baseDamage': 15,                       # 基础伤害值
            'headshotMultiplier': 2.0,              # 爆头伤害倍率
            'damageCurve': 'curves.template'        # 伤害随速度衰减曲线资源ID (asset uri)
        },
        # 载荷2: 爆炸 (可选)
        # {
        #     'type': 'explosive',
        #     'baseDamage': 60,                       # 爆炸中心伤害
        #     'explosionRadius': 3.0,                 # 爆炸半径 (米)
        #     'damageCurve': 'curves.damage9mm',      # 爆炸伤害曲线（乘法）
        #     'impulseForce': 5,                      # 爆炸击退力 (同样使用爆炸伤害曲线)
        #     'delayDetonationTime': 0.0,             # 延时引爆时间 (0为触发即爆)
        # },
        # 载荷3: 燃烧 (可选)
        # {
        #     'type': 'incendiary',
        #     'firePoolDamage': 15,                   # 火焰区域每跳伤害
        #     'firePoolDuration': 4.0,                # 火焰持续时间
        #     'firePoolRadius': 1.5,                  # 火焰范围半径
        #     'igniteChance': 0.7,                    # 点燃目标概率
        #     'statusDuration': 3.0                   # 燃烧异常状态持续时间
        # },
    ],

    # --- 表现资源 ---
    'fxAsset': {
        'tracer': 'fx_tracer_red',          # 曳光轨迹特效ID
        'impactDecal': 'decal_bullet_hole', # 命中表面弹孔贴花ID
        'hitFX': 'fx_impact_spark'          # 命中特效ID (物理表面)
    },
    'modelAsset': {
        'bulletEntity': '',                 # 子弹客户端实体 type string
        'casingEntity': 'casing_556'         # 弹壳模型ID (用于抛壳)
    }
}