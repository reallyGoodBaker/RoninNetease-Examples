class AnimationBlendingTypes:
    IN = 'in'
    OUT = 'out'


class AnimationEasingTypes:
    LINEAR = 'linear'
    QUAD = 'quad'
    CUBIC = 'cubic'
    QUART = 'quart'
    QUINT = 'quint'
    SINE = 'sine'
    EXPO = 'expo'


class LoopType:
    ONCE = 0
    LOOP = 1
    KEEP_LAST_FRAME = 2


class NotifyState:
    START = 1
    END = 0


class AnimExEvents:
    Notify = 'animEx:Notify'
    NotifyStart = 'animEx:NotifyStart'
    NotifyEnd = 'animEx:NotifyEnd'
    Finish = 'animEx:Finish'
    Interrupted = 'animEx:Interrupted'