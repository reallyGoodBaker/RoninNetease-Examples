from ...engine.architect.compact import (
    Plugin, PluginBase,
)


@Plugin(
    'ShooterIndicatorServer',
    [0, 0, 1],
    'RGB39',
    '射击指示器，准星和击杀图标都属于这个',
)
class ShooterIndicatorServer(PluginBase):
    def onCreate(self):
        from .systems import receiverServer