# -*- coding: utf-8 -*-

"""
AttachmentModifiers:
    recoilX             水平后坐力
    recoilY             垂直后坐力
    triggerDelay        扳机延迟
    magazineCapacity    供弹总数
    reloadTime          换弹时长
    tacticalReloadTime  战术换弹时长
    countPerClip        每个漏夹的数量
    velocityModifier    子弹初速乘数
    maxSpread           子弹最大散布角度
    spreadIncreasePerShot       每次射击增加的散布角度
    speedModifier       移动速度乘数
    adsInTime           进入开镜的时间
    adsOutTime          退出开镜的时间
    sprintToFireTime    跑射延迟
    extra               额外数据
"""

Asset = {
    'itemName': '',     # 物品名
    'modifiers': [
        { 'stat': 'recoilX', 'operation': '-', 'value': 0.2 },
        { 'stat': 'magazineCapacity', 'operation': '=', 'value': 50 },
        { 'stat': 'reloadTime', 'operation': '+', 'value': 5 },
        { 'stat': 'adsInTime', 'operation': '*', 'value': 1.5 },
        { 'stat': 'spreadIncreasePerShot', 'operation': '/', 'value': 2 },
    ],
    'features': [
        '-aiming',      # 删除瞄准功能
        '+flashlight',  # 添加战术手电
    ]
}