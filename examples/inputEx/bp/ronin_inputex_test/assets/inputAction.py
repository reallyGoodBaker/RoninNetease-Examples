from ..architect.plugins.input.enum import ValueType
from ..architect.plugins.input.utils.inputAction import InputAction
from ..architect.plugins.input.utils.modifier import DeadZone


InputAction(
    'laravelMovement', ValueType.Vector2,
    modifiers=[
        # 键盘和手柄输入的值没有归一化，所以需要通过deadzone来处理, 比如键盘会出现(1.0, 1.0), 但实际上这个长度是根号2不是1
        # 手柄也是可以超过 1.0 的，可以自行尝试
        DeadZone()
    ]
)

InputAction(
    'jump', ValueType.Double,
)

InputAction(
    'startFly', ValueType.Double,
)

InputAction(
    'stopFly', ValueType.Double,
)

InputAction(
    'spying', ValueType.Double,
)

InputAction(
    'flyMove', ValueType.Vector2,
)
