from ...engine.architect.plugins.input.utils.mappingContext import (
    InputMapping, InputBinding, InputType
)
from ...engine.architect.plugins.input.enum import KeyboardKey
from ...engine.architect.plugins.input.utils.trigger import TriggerDown

Asset = InputMapping(
    'mapping.bayonet', [
        InputBinding(
            InputType.Key,
            KeyboardKey.F,
            'action.bayonet',
            triggers=[
                TriggerDown()
            ]
        )
    ]
)