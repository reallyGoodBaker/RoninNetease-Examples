from ...core.loader import Plugin, PluginBase

@Plugin(
    'RoninAnimationExServer',
    [ 1, 0, 0 ],
    'RGB39',
    'Anim Seq & Montage'
)
class AnimationExServerPlugin(PluginBase):
    def onCreate(self):
        from .systems.serverSync import AnimExServer