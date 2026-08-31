from ....engine.architect.compact import (
    UiSubsystem, UiDef, AutoCreate, Hud,
    signal, Sink,
    addTimer,
)
from ....engine.architect.math.double import clamp, lerp
from ....engine.architect.math.utils import screenSize


HIT_DURATION = 0.15
KILL_DURATION = 0.15


class IndicatorType:
    Hit = 0
    Kill = 1


hit, setHit = signal(0)
kill, setKill = signal(0)
killedEntities = set()


@AutoCreate
@UiDef('shooter_indicator.main')
@Hud
class PlayerIndicatorHud(UiSubsystem):

    hitRemains = 0
    killRemains = 0

    def onCreate(self):
        self.canTick = True
        self.hit = self.find('/hit')
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

    def onShowHitEffect(self, ev):
        target = ev.target
        if target in killedEntities:
            return

        isHeadShot = ev.isHeadShot
        kill = ev.kill
        if kill:
            killedEntities.add(target)
            addTimer(1, lambda: killedEntities.remove(target), False)

        color = isHeadShot and (1, 1, 0) or kill and (1, 0, 0) or (1, 1, 1)

        if kill:
            self.setIndicatorColor(self.kill, color)
            self.killRemains = KILL_DURATION
            self.kill.SetVisible(True)
        else:
            self.setIndicatorColor(self.hit, color)
            self.hitRemains = HIT_DURATION
            self.hit.SetVisible(True)

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
