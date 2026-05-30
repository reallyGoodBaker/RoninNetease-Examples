from ..core.annotation import AnnotationHelper
from ..conf import UI_DEF, UI_SINK, UI_NAMESPACE, UI_SCREEN, UI_HUD, UI_GESTURE
from ..event import EventSignal, EventTarget
from ..core.ref import Ref
from ..core.basic import clientApi
from ..level.client import LevelClient
from ..core.subsystem import ClientSubsystem, SubsystemManager, subsystem

from .gesture import GestureBinder, TouchEvents, Touch

class SinkContext(object):
    contextStack = [] # type: list[SinkContext]

    @staticmethod
    def stackTop():
        if len(SinkContext.contextStack) > 0:
            return SinkContext.contextStack[-1]
        return None

    def __init__(self, initiator):
        self.deps = [] # type: list[EventSignal]
        self._initiator = initiator
        SinkContext.contextStack.append(self)
        initiator()
        SinkContext.contextStack.pop()

    def _removeDepListeners(self):
        for dep in self.deps:
            dep.off(self._initiator)

    def __enter__(self):
        return self

    def recordDep(self, dep):
        # type: (EventSignal) -> None
        if dep in self.deps:
            return
        self.deps.append(dep)
        dep.on(self._initiator)


def UiDef(uiDef):
    def decorator(cls):
        AnnotationHelper.addAnnotation(cls, UI_DEF, uiDef)
        cls._handleUiDef(uiDef)
        return cls
    return decorator


def AutoCreate(cls):
    cls._handleAutoCreate()
    return cls


def Screen(cls):
    AnnotationHelper.addAnnotation(cls, UI_SCREEN, True)
    return cls


def Hud(cls):
    AnnotationHelper.addAnnotation(cls, UI_HUD, True)
    return cls


def Sink(method):
    """
    @Sink 在控件初始化时会自动调用一遍用来获取控件依赖，之后在控件依赖发生变化时，会自动调用一遍。

    如果你不希望某个响应式对象被加入依赖，只需要在 getter 执行前return即可。
    """
    AnnotationHelper.addAnnotation(method, UI_SINK, True)
    return method


def signal(defaultValue=None, updater=None): # type: ignore
    # type: (object, function) -> tuple[function, function]
    """
    用于object时, 由于修改object内字段不会导致object的hash值变化, 因此不会触发依赖更新。

    你需要通过手动设置 updater(val: T, oldVal: T): T 来让系统强制更新依赖值。
    """
    val = Ref(defaultValue)
    dep = EventSignal()
    def getter():
        top = SinkContext.stackTop()
        if top:
            top.recordDep(dep)
        return val.value
    def setter(v):
        if updater:
            newVal = updater(v, val.value) # type: ignore
            val.value = newVal
            dep.emit()
        else:
            if v != val.value:
                val.value = v
                dep.emit()
    return (getter, setter) # type: ignore


def reactive(obj):
    # type: (object) -> tuple[function, function]
    """
    仅用于新式类 (继承自 object)
    """
    getVal, setVal = signal()
    def wrapSetattr(obj):
        objClass = obj.__class__
        previous = objClass.__setattr__
        def newSetattr(self, name, value):
            setVal(value) # type: ignore
            previous(self, name, value)
        objClass.__setattr__ = newSetattr
    wrapSetattr(obj)
    return (getVal, setVal)


ScreenNode = clientApi.GetScreenNodeCls()
class UiSubsystem(ScreenNode, ClientSubsystem, EventTarget):
    def __init__(self, engine, system, params):
        manager = SubsystemManager.getInstance()
        ScreenNode.__init__(self, engine, system, params) # type: ignore
        ClientSubsystem.__init__(self, manager.system, manager.engine, manager.sysName) # type: ignore
        EventTarget.__init__(self)
        manager._record(self) # type: ignore
        self.params = params
        self.rootControl = None
        self._foundControls = {}
        self._sinks = {} # type: dict[function, SinkContext]

    @classmethod
    def _handleUiDef(cls, uiDef):
        def defineAsync():
            def _define(_):
                cls.defineUi(uiDef)
            subsystem.addListener('UiInitFinished', _define) # type: ignore

        game = LevelClient.getInstance().game
        game.AddTimer(0, defineAsync) # type: ignore

    @classmethod
    def _handleAutoCreate(cls):
        def createAsync():
            isScreen = AnnotationHelper.getAnnotation(cls, UI_SCREEN)
            isHud = AnnotationHelper.getAnnotation(cls, UI_HUD)
            def _createUi(_):
                cls.defineUi(AnnotationHelper.getAnnotation(cls, UI_DEF))
                if isScreen:
                    cls.pushScreen()
                elif isHud:
                    cls.create(isHud=1)
                else:
                    cls.create(isHud=0)
            subsystem.addListener('UiInitFinished', _createUi) # type: ignore

        game = LevelClient.getInstance().game
        game.AddTimer(0, createAsync) # type: ignore

    ns = UI_NAMESPACE
    inst = None

    def _initGesture(self):
        for method in AnnotationHelper.findAnnotatedMethods(self, UI_GESTURE):
            type, controlPath = AnnotationHelper.getAnnotation(method, UI_GESTURE) # type: ignore
            self.addEventListener(controlPath, type, method)

    @classmethod
    def defineUi(cls, uiDef):
        try:
            clientApi.RegisterUI(
                cls.ns,
                cls.__name__,
                cls.__module__ + '.' + cls.__name__,
                uiDef
            )
        except Exception as e:
            return

    @classmethod
    def getOrCreate(cls, **params):
        if cls.inst:
            return cls.inst

        ui = clientApi.CreateUI(cls.ns, cls.__name__, params) # type: ignore
        cls.inst = ui
        return ui

    @classmethod
    def create(cls, **params):
        if cls.inst:
            cls.inst.remove() # type: ignore
        ui = clientApi.CreateUI(cls.ns, cls.__name__, params) # type: ignore
        return ui

    @classmethod
    def pushScreen(cls, **params):
        params['pushScreen'] = True
        ui = clientApi.PushScreen(cls.ns, cls.__name__, params)
        cls.inst = ui
        return ui

    def find(self, path):
        if path in self._foundControls:
            return self._foundControls[path]
        else:
            ctrl = self.GetBaseUIControl(path)
            self._foundControls[path] = ctrl
            return ctrl

    def findByName(self, name):
        return self.rootControl.GetChildByName(name) # type: ignore

    def _handleGamepadBack(self, ev):
        if not self.GetIsHud() and ev.key == 2 and ev.isDown:
            self._performBackPressed()

    def _handleKeyboardBack(self, ev):
        if not self.GetIsHud() and ev.key == '27' and ev.isDown:
            self._performBackPressed()

    def _initSinks(self):
        for method in AnnotationHelper.findAnnotatedMethods(self, UI_SINK):
            initiator = method.__get__(self)
            ctx = SinkContext(initiator)
            self._sinks[method] = ctx

    def _removeSinks(self):
        for method in AnnotationHelper.findAnnotatedMethods(self, UI_SINK):
            ctx = self._sinks.get(method)
            if ctx:
                ctx._removeDepListeners()

    def Create(self):
        self.rootControl = self.GetBaseUIControl('/')
        self.onCreate()
        self.listen('OnBackButtonReleaseClientEvent', self._performBackPressed) # type: ignore
        self.listen('OnGamepadKeyPressClientEvent', self._handleGamepadBack) # type: ignore
        self.listen('OnKeyPressInGame', self._handleKeyboardBack) # type: ignore
        self._initSinks()
        self._initGesture()

    def Destroy(self):
        self.removeAllListener()
        self._removeSinks()
        self.unlisten('OnBackButtonReleaseClientEvent', self._performBackPressed) # type: ignore
        self.unlisten('OnGamepadKeyPressClientEvent', self._handleGamepadBack) # type: ignore
        self.unlisten('OnKeyPressInGame', self._handleKeyboardBack) # type: ignore
        self.onDestroy()
        SubsystemManager.getInstance().removeSubsystem(self.__class__) # type: ignore

    def remove(self):
        if self.params.get('pushScreen'):
            clientApi.PopScreen()
        else:
            self.SetRemove()

    def _performBackPressed(self, *_):
        shouldPrevent = bool(self.onBackPressed())
        if not shouldPrevent and not self.GetIsHud():
            self.remove()

    def onCreate(self):
        pass

    def onBackPressed(self):
        # type: () -> bool
        return False

    def onDestroy(self):
        pass

    def addEventListener(self, controlPath, type, handler, opt=None):
        """
        此方法会把 handler 的 self 绑定到当前 UiSubsystem 实例
        """
        control = self.find(controlPath)
        if type in TouchEvents:
            control.asButton().AddTouchEventParams(opt) # type: ignore
        GestureBinder[type](self, control)
        def _handlerWrapper(ev, _method=handler.__get__(self), _control=control):
            if ev.control == _control:
                _method(ev)
        self.addListener(type, _handlerWrapper)

