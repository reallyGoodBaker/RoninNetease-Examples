from ....compact import LevelClient, clientApi, compClient, ClientSubsystem, SubsystemClient, getOneSingletonComponent, EventListener, localPlayerId
from ....compact import vec, moduloSqrt
from ..utils.mappingContext import InputMapping
from ..utils.inputValue import InputValue
from ..utils.inputAction import InputAction
from ..utils.trigger import InputTrigger
from ..components.inputEx import InputExComponent
from ..enum import TouchAxis, TouchType, GamepadAxis, MouseAxis, MouseKey, AccumulationBehavior, InputType, TriggerState, TriggerCombineType, InputState, IA_EVENT_PREFIX


class _TransState:
    Empty = 0
    Started = 1
    Triggered = 2
    Completed = 3
    Canceled = 4
    Ongoing = 5
    StartedAndTriggered = 6


_StateTransResultMapping = {
    (TriggerState.Empty, TriggerState.Empty):           (_TransState.Empty,                 InputState.Empty),
    (TriggerState.Empty, TriggerState.Ongoing):         (_TransState.Started,               InputState.Started),
    (TriggerState.Empty, TriggerState.Triggered):       (_TransState.StartedAndTriggered,   InputState.Triggered),
    (TriggerState.Ongoing, TriggerState.Empty):         (_TransState.Canceled,              InputState.Canceled),
    (TriggerState.Ongoing, TriggerState.Ongoing):       (_TransState.Ongoing,               InputState.Ongoing),
    (TriggerState.Ongoing, TriggerState.Triggered):     (_TransState.Triggered,             InputState.Triggered),
    (TriggerState.Triggered, TriggerState.Empty):       (_TransState.Completed,             InputState.Completed),
    (TriggerState.Triggered, TriggerState.Triggered):   (_TransState.Triggered,             InputState.Triggered),
    (TriggerState.Triggered, TriggerState.Ongoing):     (_TransState.Ongoing,               InputState.Ongoing)
}


_AllowlistMapping = (
    (InputType.Key, 0),
    (InputType.Touch, 1),
    (InputType.Gamepad, 2),
)


def checkIfAllow(inputType, inputMode, bindKey):
    _firstReturn = (inputType, inputMode) in _AllowlistMapping
    if _firstReturn:
        return True
    if inputType != InputType.Axis:
        return False
    if inputMode == 0:
        return bindKey in (MouseAxis.Pos, MouseAxis.Scroll)
    if inputMode == 1:
        return bindKey in (TouchAxis.Pos, TouchAxis.Move)
    if inputMode == 2:
        return bindKey in (GamepadAxis.LS, GamepadAxis.RS, GamepadAxis.LT, GamepadAxis.RT)
    return False



@SubsystemClient
class InputExClientSystem(ClientSubsystem):

    def onInit(self):
        self.canTick = True
        self._iaEvents = set()
        self.localActorMotion = compClient.CreateActorMotion(localPlayerId())
        self.playerView = LevelClient.getInstance().playerView
        self.inputMode = 0
        self._mousePos = None
        self._touchPos = None


    def isMouseInput(self):
        return self.inputMode == 0
    

    def isGamepadInput(self):
        return self.inputMode == 2
    

    def isTouchInput(self):
        return self.inputMode == 1


    def _updateMapping(self, mapping, inputEx, dt):
        # type: (InputMapping, InputExComponent, float) -> None
        inputEx.actionValues.clear()
        self._iaEvents.clear()
        for binding in mapping.bindings:
            if not checkIfAllow(binding.inputType, self.inputMode, binding.key):
                continue
            value = inputEx.getInputValue(binding.inputType, binding.key) # type: InputValue
            modifiedValue = value.rawValue[:]
            for modifier in binding.modifiers:
                modifiedValue = modifier.doModify(modifiedValue)
            self._handleAction(value, inputEx, binding.action, modifiedValue, dt, binding.triggers)
        for actionName, transState, inputState in self._iaEvents:
            self._dispatchIAEvent(transState, inputState, actionName, inputEx)


    def _evalTriggers(self, dt, inputVal, prevState, mappingTriggers, actionTriggers):
        # type: (float, InputValue, TriggerState, list[InputTrigger], list[InputTrigger]) -> TriggerState
        """
        综合判断触发器状态
        规则: 默认为 Empty, 任意一个 Trigger 返回 Ongoing 时切换到 Ongoing,
        所有隐式 Trigger 返回 Triggered 且任意一个显式 Trigger 返回 Triggered 时切换到 Triggered,
        所有 Trigger 返回 Empty 时切换到 Empty
        """
        _ongoings = 0
        _emptyTriggers = 0
        _implicitsSize = 0
        _explicitsSize = 0
        _triggeredImplicits = 0
        _triggeredExplicits = 0
        allTriggers = mappingTriggers + actionTriggers

        if len(allTriggers) == 0:
            return TriggerState.Empty

        for trigger in allTriggers:
            if trigger.combineType == TriggerCombineType.And:
                _implicitsSize += 1
                triggerState = trigger.updateState(inputVal, dt)
                if triggerState == TriggerState.Ongoing:
                    _ongoings += 1
                elif triggerState == TriggerState.Triggered:
                    _triggeredImplicits += 1
                elif triggerState == TriggerState.Empty:
                    _emptyTriggers += 1
            elif trigger.combineType == TriggerCombineType.Or:
                _explicitsSize += 1
                triggerState = trigger.updateState(inputVal, dt)
                if triggerState == TriggerState.Ongoing:
                    _ongoings += 1
                elif triggerState == TriggerState.Triggered:
                    _triggeredExplicits += 1
                elif triggerState == TriggerState.Empty:
                    _emptyTriggers += 1

        curTriggerState = TriggerState.Empty
        # Trigger: And triggers 必须全部为 Triggered, Or 触发器只要有一个为 Triggered 即可
        if _triggeredImplicits == _implicitsSize and (_explicitsSize == 0 or _triggeredExplicits > 0):
            curTriggerState = TriggerState.Triggered
        # Ongoing: 只要有一个触发器为 Ongoing, 则为 Ongoing
        elif _ongoings > 0:
            curTriggerState = TriggerState.Ongoing
        else:
            curTriggerState = TriggerState.Empty

        _transState, _inputState = _StateTransResultMapping.get((prevState, curTriggerState), (_TransState.Empty, InputState.Empty))
        return curTriggerState, _transState, _inputState


    def _dispatchIAEvent(self, transState, inputState, actionName, inputEx):
        # type: (_TransState, InputState, str, InputExComponent) -> None
        valVec = inputEx.actionValues[actionName]
        if transState == 0:
            return
        ia = InputAction.get(actionName)
        for modifier in ia.modifiers:
            valVec = modifier.doModify(valVec)
        value = InputValue.value(valVec, ia.valueType)
        evNamePrefix = IA_EVENT_PREFIX + actionName
        if transState != inputState:
            self.broadcast(evNamePrefix + str(InputState.Started), { 'value': value })
            self.broadcast(evNamePrefix + str(InputState.Triggered), { 'value': value })
        else:
            self.broadcast(evNamePrefix + str(inputState), { 'value': value })


    def _mixIAValue(self, ia, prevValue, value):
        # type: (InputAction, tuple[float, float, float], tuple[float, float, float]) -> tuple[float, float, float]
        if ia.accBehavior == AccumulationBehavior.Override:
            return value
        elif ia.accBehavior == AccumulationBehavior.Cumulative:
            px, py, pz = prevValue
            vx, vy, vz = value
            return (px + vx, py + vy, pz + vz)
        elif ia.accBehavior == AccumulationBehavior.HighestAbsValue:
            px, py, pz = prevValue
            vx, vy, vz = value
            return (
                px if abs(px) > abs(vx) else vx,
                py if abs(py) > abs(vy) else vy,
                pz if abs(pz) > abs(vz) else vz
            )


    def _handleAction(self, inputValue, inputEx, actionName, value, dt, mappingTriggers):
        # type: (InputValue, InputExComponent, str, tuple[float, float, float], float, list[InputTrigger]) -> None
        ia = InputAction.get(actionName) # type: InputAction
        if not ia:
            return

        prevState = inputEx._triggerStates.get(actionName, TriggerState.Empty)
        actionValue = inputEx.actionValues.get(actionName, (0.0, 0.0, 0.0))
        curTriggerState, transState, inputState = self._evalTriggers(dt, inputValue, prevState, mappingTriggers, ia.triggers)
        newActionValue = self._mixIAValue(ia, actionValue, value)
        inputEx.actionValues[actionName] = newActionValue
        inputEx._triggerStates[actionName] = curTriggerState
        self._iaEvents.add((actionName, transState, inputState))


    def updateMapping(self, inputEx, deltaTime):
        for mapping in inputEx.inputMappings:
            self._updateMapping(mapping, inputEx, deltaTime)


    def _updateMousePos(self, inputEx):
        # type: (InputExComponent) -> None
        mousePos = self.localActorMotion.GetMousePosition()
        if not mousePos:
            return
        x, y = mousePos
        if self._mousePos is None:
            self._mousePos = vec(x, y, 0.0)
            return
        curPos = vec(x, y, 0.0)
        delta = curPos - vec(self._mousePos)
        self._mousePos = curPos
        inputEx.updateInputValue(InputType.Axis, MouseAxis.Pos, (x, y, 0.0))
        inputEx.updateInputValue(InputType.Axis, MouseAxis.Move, (delta.x, delta.y, 0.0))

    def _updateTouchPos(self, inputEx):
        # type: (InputExComponent) -> None
        x, y = clientApi.GetTouchPos()
        curPos = vec(x, y, 0.0)
        if self._touchPos is None:
            self._touchPos = curPos
            return
        delta = curPos - vec(self._touchPos)
        self._touchPos = curPos
        inputEx.updateInputValue(InputType.Axis, TouchAxis.Pos, (x, y, 0.0))
        inputEx.updateInputValue(InputType.Axis, TouchAxis.Move, (delta.x, delta.y, 0.0))


    def onRender(self, dt):
        self.inputMode = self.playerView.GetToggleOption('INPUT_MODE')
        inputEx = getOneSingletonComponent(InputExComponent)
        if not inputEx:
            return
        self._updateMousePos(inputEx)
        self._updateTouchPos(inputEx)
        self.updateMapping(inputEx, dt)


    @EventListener('OnKeyPressInGame')
    def onKeyboardPress(self, ev):
        key = int(ev.key)
        isDown = int(ev.isDown)
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Key, key, (isDown, 0.0, 0.0))


    @EventListener('OnGamepadKeyPressClientEvent')
    def onGamepadPress(self, ev):
        button = ev.key
        isDown = int(ev.isDown)
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Gamepad, button, (isDown, 0.0, 0.0))


    @EventListener('OnGamepadStickClientEvent')
    def onGamepadStick(self, ev):
        stick = ev.key
        x = ev.x
        y = ev.y
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Axis, stick, (x, y, 0.0))


    @EventListener('OnGamepadTriggerClientEvent')
    def onGamepadTrigger(self, ev):
        key = ev.key
        value = ev.magnitude
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Axis, key, (value, 0.0, 0.0))


    @EventListener('RightClickBeforeClientEvent')
    def onRightClick(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        if self.isMouseInput():
            inputEx.updateInputValue(InputType.Key, MouseKey.Right, (1.0, 0.0, 0.0))
        if inputEx.preventUse:
            ev.prevent()


    @EventListener('RightClickReleaseClientEvent')
    def onRightRelease(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        if self.isMouseInput():
            inputEx.updateInputValue(InputType.Key, MouseKey.Right, (0.0, 0.0, 0.0))


    @EventListener('LeftClickBeforeClientEvent')
    def onLeftClick(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        if self.isMouseInput():
            inputEx.updateInputValue(InputType.Key, MouseKey.Left, (1.0, 0.0, 0.0))
        if inputEx.preventAttack:
            ev.prevent()


    @EventListener('LeftClickReleaseClientEvent')
    def onLeftRelease(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        if self.isMouseInput():
            inputEx.updateInputValue(InputType.Key, MouseKey.Left, (0.0, 0.0, 0.0))


    @EventListener('OnMouseMiddleDownClientEvent')
    def onMiddleClick(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Key, MouseKey.Middle, (ev.isDown, 0.0, 0.0))


    @EventListener('MouseWheelClientEvent')
    def onMouseWheel(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        delta = ev.direction if ev.direction > 0 else -1
        inputEx.updateInputValue(InputType.Axis, MouseAxis.Scroll, (delta, 0.0, 0.0))


    @EventListener('TapBeforeClientEvent')
    def onTap(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Touch, TouchType.Tap, (1.0, 0.0, 0.0))
        if inputEx.preventTap:
            ev.prevent()


    @EventListener('HoldBeforeClientEvent')
    def onHold(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Touch, TouchType.Hold, (1.0, 0.0, 0.0))
        if inputEx.preventHold:
            ev.prevent()


    @EventListener('TapOrHoldReleaseClientEvent')
    def onTapOrHoldRelease(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.updateInputValue(InputType.Touch, TouchType.Tap, (0.0, 0.0, 0.0))
        inputEx.updateInputValue(InputType.Touch, TouchType.Hold, (0.0, 0.0, 0.0))