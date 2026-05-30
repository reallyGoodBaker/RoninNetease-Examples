from ..architect.plugins.input.utils.mappingContext import InputMapping, InputBinding
from ..architect.plugins.input.enum import InputType, MouseKey
from ..architect.plugins.input.utils.trigger import TriggerPressed


InputMapping(
    'IM_Attack', [
        InputBinding(
            InputType.Key, MouseKey.Left,
            'IA_Attack',
            triggers=[
                TriggerPressed(),
            ]
        )
])