from ..architect.plugins.input.enum import MouseKey, InputType, KeyboardKey, AxisSwizzleOrder, GamepadAxis, GamepadKey
from ..architect.plugins.input.utils.mappingContext import InputMapping, InputBinding
from ..architect.plugins.input.utils.modifier import SwizzleAxis, Negate
from ..architect.plugins.input.utils.trigger import TriggerDown, DoubleTap, TriggerHold


InputMapping(
    'move', [
        # Laravel Movement
        InputBinding(
            InputType.Key, KeyboardKey.W,
            'laravelMovement',
            # 键盘输入的值不是布尔值, 而是一个Vector3, (isDown, 0.0, 0.0), 通过把x换到y轴，可以实现两个轴的复合输入
            modifiers=[ SwizzleAxis(order=AxisSwizzleOrder.YXZ) ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.S,
            'laravelMovement',
            modifiers=[
                SwizzleAxis(order=AxisSwizzleOrder.YXZ),
                # 键盘输入的值只能是0.0或者1.0, 所以把值取反就能得到一个轴的正负方向输入
                Negate()
            ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.D,
            'laravelMovement',
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.A,
            'laravelMovement',
            modifiers=[ Negate() ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            # 由于我们的wasd输入轴的布局和手柄输入轴完全一致，这里手柄输入可以不做修改
            InputType.Axis, GamepadAxis.LS,
            'laravelMovement',
            triggers=[ TriggerDown() ],
        ),

        # Jump
        InputBinding(
            InputType.Key, KeyboardKey.Space,
            'jump',
            # 按下跳跃会一直处于跳跃状态，我们在监听中处理是否跳跃
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Gamepad, GamepadKey.A,
            'jump',
            triggers=[ TriggerDown() ],
        ),

        # 切换飞行
        InputBinding(
            InputType.Key, KeyboardKey.Space,
            'startFly',
            triggers=[ DoubleTap() ],
        ),
        InputBinding(
            InputType.Gamepad, GamepadKey.A,
            'startFly',
            triggers=[ DoubleTap() ],
        ),
    ]
)


InputMapping(
    'fly', [
        InputBinding(
            InputType.Key, KeyboardKey.W,
            'flyMove',
            modifiers=[ SwizzleAxis(order=AxisSwizzleOrder.YXZ) ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.S,
            'flyMove',
            modifiers=[
                SwizzleAxis(order=AxisSwizzleOrder.YXZ),
                Negate()
            ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.D,
            'flyMove',
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Key, KeyboardKey.A,
            'flyMove',
            modifiers=[ Negate() ],
            triggers=[ TriggerDown() ],
        ),
        InputBinding(
            InputType.Axis, GamepadAxis.LS,
            'flyMove',
            triggers=[ TriggerDown() ],
        ),

        InputBinding(
            InputType.Key, KeyboardKey.Space,
            'stopFly',
            triggers=[ DoubleTap() ],
        ),
        InputBinding(
            InputType.Gamepad, GamepadKey.A,
            'stopFly',
            triggers=[ DoubleTap() ],
        ),
    ]
)


InputMapping(
    'spying', [
        # 长按右键或LT一秒进入缩放
        InputBinding(
            InputType.Key, MouseKey.Right,
            'spying',
            triggers=[ TriggerHold(1) ],
        ),
        InputBinding(
            InputType.Axis, GamepadAxis.LT,
            'spying',
            triggers=[ TriggerHold(1) ],
        ),
    ]
)