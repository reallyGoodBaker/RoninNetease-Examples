# -*- coding: utf-8 -*-

"""
AttachmentModifiers:
    recoilX             水平后坐力
    recoilY             垂直后坐力
    triggerDelay        扳机延迟
    magazineCapacity    供弹总数
    reloadModes         换弹模式 (这个 modifier 只支持 '=')
    velocityModifier    子弹初速乘数
    spread              准星散布
    speedModifier       移动速度乘数
    adsIn               进入开镜的时间
    adsOut              退出开镜的时间
    sprintToFireTime    跑射延迟
    extra               额外数据
"""

Asset = {
    'attachmentId': 'attachement.template', # 配件id，必须唯一，同名会覆盖
    'bindItem': '',         # 物品名，可以为空
    'category': 'none',  # 配件 category, 用于匹配可用配件
    'displayName': '',
    'texture': '',
    'modifiers': [
        { 'stat': 'recoilX', 'operation': '-', 'value': 0.2 },
        { 'stat': 'magazineCapacity', 'operation': '=', 'value': 50 },
        { 'stat': 'reloadTime', 'operation': '+', 'value': 5 },
        { 'stat': 'adsInTime', 'operation': '*', 'value': 1.5 },
        { 'stat': 'spreadIncreasePerShot', 'operation': '/', 'value': 2 },
    ],
    '-features': [
        'aiming',       # 删除瞄准功能
    ],
    '+features': [
        'tacticalStance',
        {
            'name': 'flashlight',
            'params': {
                'angle': 30
            }
        },
    ],
    'extraSlot': [
        # 定义于武器 slots 字段完全相同
    ]
}