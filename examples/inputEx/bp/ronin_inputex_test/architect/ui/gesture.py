from ..core.annotation import AnnotationHelper
from ..event.core import ChainedEvent
from ..conf import UI_GESTURE

def _btnDecoratorBuilder(type):
    @staticmethod
    def decorator(btnPath):
        def wrapper(func):
            AnnotationHelper.addAnnotation(func, UI_GESTURE, (type, btnPath))
            return func
        return wrapper
    return decorator


class Touch(object):
    Click = _btnDecoratorBuilder('click')
    Move = _btnDecoratorBuilder('move')
    MoveIn = _btnDecoratorBuilder('movein')
    MoveOut = _btnDecoratorBuilder('moveout')
    Cancel = _btnDecoratorBuilder('cancel')
    Down = _btnDecoratorBuilder('down')


TouchEvents = (
    'click',
    'down',
    'move',
    'movein',
    'moveout',
    'cancel'
)


def _createGestureBinder(type, bindingFuncName, castFuncName):
    def _binder(screen, control):
        casted = getattr(control, castFuncName)()
        bindingFunc = getattr(casted, bindingFuncName)
        def _listener(_ev={}, target=casted, screen=screen):
            _ev['target'] = target
            _ev['control'] = control
            _ev['screen'] = screen
            _ev['x'] = _ev.get('TouchPosX')
            _ev['y'] = _ev.get('TouchPosY')
            _ev['pos'] = (_ev['x'], _ev['y'])
            ev = ChainedEvent(type, _ev)
            screen.dispatch(type, ev)
        bindingFunc(_listener)
    return _binder


GestureBinder = {
    'click': _createGestureBinder('click', 'SetButtonTouchUpCallback', 'asButton'),
    'down': _createGestureBinder('down', 'SetButtonTouchDownCallback', 'asButton'),
    'move': _createGestureBinder('move', 'SetButtonTouchMoveCallback', 'asButton'),
    'movein': _createGestureBinder('movein', 'SetButtonTouchMoveInCallback', 'asButton'),
    'moveout': _createGestureBinder('moveout', 'SetButtonTouchMoveOutCallback', 'asButton'),
    'cancel': _createGestureBinder('cancel', 'SetButtonTouchCancelCallback', 'asButton'),
}
