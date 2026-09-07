import math

from ....engine.architect.compact import (
    UiSubsystem, UiDef, AutoCreate, Hud,
    UiSizeTrackPlayer, UiTranslateTrackPlayer, UiTrackAnimation, UiAlphaTrackPlayer,
    signal, Sink,
    addTimer,
    vec,
    LevelClient, compClient,
    getEntityNameLocale,
)
from ....engine.architect.math.double import clamp, lerp
from ....engine.architect.math.utils import screenSize

# TODO: Remove these
from mod.client.ui.controls.baseUIControl import BaseUIControl


HIT_DURATION = 0.15
KILL_DURATION = 0.15


class IndicatorType:
    Hit = 0
    Kill = 1


hit, setHit = signal(0)
kill, setKill = signal(0)
killedEntities = set()


HEAD_SHOOT = (1, 0.6, 0)
KILL = (1, 0, 0)
NORMAL_HIT = (1, 1, 1)


@AutoCreate
@UiDef('shooter_indicator.main')
@Hud
class PlayerIndicatorHud(UiSubsystem):

    hitRemains = 0
    killRemains = 0

    damageVisual = 0
    damageAcc = 0
    damageRemains = 0
    damageVisible = 0
    damageAlpha = 0

    infoRemains = 0
    infoVisible = 0
    infoAlpha = 0

    def onCreate(self):
        self.canTick = True
        self.game = LevelClient.getInstance().game
        self.killIndicators = KillIndicatorController(self)
        self.hit = self.find('/hit')
        self.damage = self.find('/info_board/damage').asLabel()
        self.info = self.find('/info_board/info').asLabel()
        self.hitImages = [
            self.hit.GetChildByName('tr').asImage(),
            self.hit.GetChildByName('tl').asImage(),
            self.hit.GetChildByName('br').asImage(),
            self.hit.GetChildByName('bl').asImage()
        ]
        self.hit.SetVisible(False)

        self.kill = self.find('/kill')
        self.killImages = [
            self.kill.GetChildByName('tr').asImage(),
            self.kill.GetChildByName('tl').asImage(),
            self.kill.GetChildByName('br').asImage(),
            self.kill.GetChildByName('bl').asImage()
        ]
        self.kill.SetVisible(False)
        # 用 screenSize 的一半作为屏幕中心绝对定位
        screenWidth, screenHeight = screenSize()
        self._lastScreenSize = (screenWidth, screenHeight)
        # SetPosition 是左上角定位，要居中需要减去半尺寸
        panelHalf = 8.0 / 2.0
        self.hit.SetPosition((screenWidth / 2.0 - panelHalf, screenHeight / 2.0 - panelHalf))
        self.kill.SetPosition((screenWidth / 2.0 - panelHalf, screenHeight / 2.0 - panelHalf))
        self._addListener('showHitEffect', self.onShowHitEffect, True)

    def updateDamageText(self, dt):
        if self.damageRemains <= 0:
            self.damageVisible = 0
            self.damageVisual = 0
            self.damageAcc = 0
            return
        self.damageVisible = 1
        self.damageRemains = clamp(self.damageRemains - dt, 0, 6)
        t = 1 - math.exp(-10 * dt)
        value = lerp(self.damageVisual, self.damageAcc, t)
        self.damageVisual = value
        self.damage.SetText(str(int(math.ceil(value))))

    def updateDamageFade(self, dt):
        t = 1 - math.exp(-20 * dt)
        self.damageAlpha = lerp(self.damageAlpha, self.damageVisible, t)
        self.damage.SetAlpha(self.damageAlpha)

    def onShowHitEffect(self, ev):
        target = ev.target
        if target in killedEntities:
            return

        isHeadShot = ev.isHeadShot
        kill = ev.kill
        if kill:
            killedEntities.add(target)
            addTimer(1, lambda: killedEntities.remove(target), False)

        color = isHeadShot and HEAD_SHOOT or kill and KILL or NORMAL_HIT

        if kill:
            self.setIndicatorColor(self.kill, color)
            self.killRemains = KILL_DURATION
            self.kill.SetVisible(True)
            self.killIndicators.addKill(isHeadShot)
        else:
            self.setIndicatorColor(self.hit, color)
            self.hitRemains = HIT_DURATION
            self.hit.SetVisible(True)

        self.damageAcc += ev.damage
        self.damageRemains = 6
        self.showInfoLabel(target, ev.damage)

    def showInfoLabel(self, target, damage):
        self.infoRemains = 5
        self.infoVisible = 1
        self.info.SetText('「' + getEntityNameLocale(target) + '」   +' + str(int(math.ceil(damage))))

    def updateInfoAlpha(self, dt):
        t = 1 - math.exp(-20 * dt)
        self.infoAlpha = lerp(self.infoAlpha, self.infoVisible * 0.8, t)
        self.info.SetAlpha(self.infoAlpha)

    def updateInfoVisible(self, dt):
        self.infoRemains = clamp(self.infoRemains - dt, 0, 10)
        if self.infoRemains <= 0:
            self.infoVisible = 0

    def onRender(self, dt):
        # 屏幕大小变化时重新居中
        sw, sh = screenSize()
        if self._lastScreenSize != (sw, sh):
            self._lastScreenSize = (sw, sh)
            panelHalf = 8.0 / 2.0
            self.hit.SetPosition((sw / 2.0 - panelHalf, sh / 2.0 - panelHalf))
            self.kill.SetPosition((sw / 2.0 - panelHalf, sh / 2.0 - panelHalf))
        self.hitRemains = clamp(self.hitRemains - dt, 0, 999)
        self.killRemains = clamp(self.killRemains - dt, 0, 999)
        setHit(self.hitRemains / HIT_DURATION)
        setKill(self.killRemains / KILL_DURATION)
        self.updateDamageText(dt)
        self.updateDamageFade(dt)
        self.updateInfoAlpha(dt)
        self.updateInfoVisible(dt)

    def setIndicatorColor(self, type, color):
        # type: (IndicatorType, tuple) -> None
        images = type == IndicatorType.Hit and self.hitImages or self.killImages
        for img in images:
            img.SetSpriteColor(color)

    def setIndicatorPos(self, type, offset):
        # type: (IndicatorType, float) -> None
        # 子图 SetPosition 是相对面板左上角
        # 面板已居中，图片中心要落在目标点，需要减去 (childHalf - panelHalf)
        # childHalf=6, panelHalf=4, 所以减 2
        images = type == IndicatorType.Hit and self.hitImages or self.killImages
        images[0].SetPosition((offset - 2, -offset - 2))
        images[1].SetPosition((-offset - 2, -offset - 2))
        images[2].SetPosition((offset - 2, offset - 2))
        images[3].SetPosition((-offset - 2, offset - 2))

    @Sink
    def drawHitEffect(self):
        hitRemains = hit()
        if hitRemains <= 0:
            self.hit.SetVisible(False)
            return
        size = lerp(10, 12, hitRemains)
        self.setIndicatorPos(IndicatorType.Hit, size)

    @Sink
    def drawKillEffect(self):
        killRemains = kill()
        if killRemains <= 0:
            self.kill.SetVisible(False)
            return
        size = lerp(10, 12, killRemains)
        self.setIndicatorPos(IndicatorType.Kill, size)


class KillIndicatorController(object):

    VISIBLE_DURATION = 5
    ANIM_SIZE_KILL_IN = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((14, 14, 0)) },
        { 'alpha': 0.01, 'value': vec((40, 40, 0)) },
        { 'alpha': 0.2, 'value': vec((14, 14, 0)) },
    ])
    ANIM_SIZE_HEAD_SHOT_IN = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((14, 14, 0)) },
        { 'alpha': 0.01, 'value': vec((58, 58, 0)) },
        { 'alpha': 0.2, 'value': vec((14, 14, 0)) },
    ])
    ANIM_SIZE_OUT = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((14, 14, 0)) },
        { 'alpha': 0.2, 'value': vec((4, 4, 0)) },
    ])

    ANIM_TRANSLATE_HALF = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((0, 0, 0)) },
        { 'alpha': 0.2, 'value': vec((7.5, 0, 0)) },
    ])
    ANIM_TRANSLATE_HULL = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((0, 0, 0)) },
        { 'alpha': 0.2, 'value': vec((15, 0, 0)) },
    ])

    ANIM_FADE_IN = UiTrackAnimation([
        { 'alpha': 0, 'value': 0 },
        { 'alpha': 0.1, 'value': 1 },
    ])
    ANIM_FADE_OUT = UiTrackAnimation([
        { 'alpha': 0, 'value': 1 },
        { 'alpha': 0.2, 'value': 0 },
    ])

    ANIM_CIRCLE_FADE_IN = UiTrackAnimation([
        { 'alpha': 0, 'value': 0 },
        { 'alpha': 0.15, 'value': 0 },
        { 'alpha': 0.3, 'value': 1 },
        { 'alpha': 0.5, 'value': 0 },
    ])
    ANIM_CIRCLE_SIZE = UiTrackAnimation([
        { 'alpha': 0, 'value': vec((14, 14, 0)) },
        { 'alpha': 0.15, 'value': vec((14, 14, 0)) },
        { 'alpha': 0.6, 'value': vec((64, 64, 0)) },
    ])

    indicators = []
    removeHandlers = []
    timers = []
    idx = 0

    def __init__(self, screen):
        # type: (UiSubsystem) -> None
        self.screen = screen
        self.templateCircle = screen.findByName('circle').asImage()
        self.templateSkull = screen.findByName('skull').asImage()
        self.templateSkullBroken = screen.findByName('skull_broken').asImage()
        self.templateCircle.SetVisible(False)
        self.templateSkull.SetVisible(False)
        self.templateSkullBroken.SetVisible(False)
        self.audio = LevelClient.getInstance().customAudio

    def findPosition(self):
        indicatorCount = len(self.indicators)
        indicatorCount += 1
        ident = (indicatorCount - 1) * 1
        totalWidth = indicatorCount * 14 + ident
        newPos = -totalWidth / 2 + 7
        for indicator in self.indicators:
            UiTranslateTrackPlayer.play(indicator, KillIndicatorController.ANIM_TRANSLATE_HALF)
        return newPos

    def popOneIndicator(self):
        fn = self.removeHandlers.pop(0)
        fn()
        for indicator in self.indicators:
            UiTranslateTrackPlayer.play(indicator, KillIndicatorController.ANIM_TRANSLATE_HALF)        

    def addKill(self, isHeadShoot):
        self.idx += 1
        parent = '/info_board/kill_indicators'
        id = 'dynamic' + str(self.idx)
        self.screen.Clone(
            isHeadShoot and self.templateSkullBroken.GetPath() or self.templateSkull.GetPath(),
            parent, id
        )
        # self.audio.PlayCustomUIMusic(
        #     'indicator.cfhs' if isHeadShoot else 'indicator.cfkill'
        # )
        self.audio.PlayCustomUIMusic(
            'indicator.head_shot' if isHeadShoot else 'indicator.kill'
        )
        skull = self.screen.find(parent + '/' + id).asImage()
        skull.SetVisible(True)
        skull.SetSpriteColor(isHeadShoot and HEAD_SHOOT or NORMAL_HIT)
        ox = self.findPosition()
        x, y = skull.GetPosition()
        skull.SetPosition((x + ox, y))

        UiAlphaTrackPlayer.play(skull, KillIndicatorController.ANIM_FADE_IN)
        UiSizeTrackPlayer.play(skull, isHeadShoot and KillIndicatorController.ANIM_SIZE_HEAD_SHOT_IN or KillIndicatorController.ANIM_SIZE_KILL_IN)
        self.indicators.append(skull)

        if isHeadShoot:
            id = 'dynamic_circle' + str(self.idx)
            self.screen.Clone(
                self.templateCircle.GetPath(),
                parent, id
            )
            circle = self.screen.find(parent + '/' + id).asImage()
            circle.SetPosition((x + ox, y))
            circle.SetVisible(True)
            circle.SetSpriteColor(HEAD_SHOOT)
            UiAlphaTrackPlayer.play(circle, KillIndicatorController.ANIM_CIRCLE_FADE_IN)
            UiSizeTrackPlayer.play(circle, KillIndicatorController.ANIM_CIRCLE_SIZE, lambda: self.screen.RemoveChildControl(circle))

        def removeSkull():
            self.indicators.remove(skull)
            self.timers.remove(timer)
            UiAlphaTrackPlayer.play(skull, KillIndicatorController.ANIM_FADE_OUT)
            UiSizeTrackPlayer.play(skull, KillIndicatorController.ANIM_SIZE_OUT, lambda: self.screen.RemoveChildControl(skull))

        self.removeHandlers.append(removeSkull)
        timer = addTimer(KillIndicatorController.VISIBLE_DURATION, self.popOneIndicator, False)
        self.timers.append(timer)
