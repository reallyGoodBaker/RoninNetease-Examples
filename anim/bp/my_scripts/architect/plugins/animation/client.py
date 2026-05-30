"""
使用 v.blendex.{动画名} 来控制混合权重
使用 v.anim_timeex.{动画名} 来控制动画时间
使用 v.notify_{通知名} = 1/0 来定义通知

可以查看docs中的图片来了解如何使用
"""


from ...core.loader import Plugin, PluginBase

@Plugin(
    'RoninAnimationEx',
    [ 1, 0, 0 ],
    'RGB39',
    'Anim Seq & Montage'
)
class AnimationExPlugin(PluginBase):
    def onCreate(self):
        from .systems.animPlay import AnimationExSubsystem