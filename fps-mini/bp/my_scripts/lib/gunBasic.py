# -*- coding: utf-8 -*-
import math
import time

from ..engine.architect.compact import (
    Asset, Async, wait, LevelClient,
    getOrCreateComponent, localPlayerId,
    TimerAdapter, addTimer, cancelTimer,
    dictx, NamedEntityVariable,
    getOrCreateSingletonComponent,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent

from .shootVfx import PlayerShooterVfxSystem
from .bullet import ClientBulletSystem
from .stats import StatMapping, stats
from .feature import LocalFeaturesComponent



class GunState:
    Hold = 0
    Firing = 1
    Reloading = 2
    Cycling = 3


class GunAutoState:
    Full = 0
    Semi = 1


class ModifierCategory(object):
    def __init__(self, cat, raw):
        self.cat = cat
        self.raw = raw
        self.attachments = {}

    def applyAttachment(self, attachment):
        id = attachment['attachmentId']
        modifiers = filter(lambda v: v['stat'] == self.cat, attachment.get('modifiers', []))
        self.attachments[id] = modifiers

    def removeAttachment(self, attachment):
        id = attachment if type(attachment) == str else attachment['attachmentId']
        self.attachments.pop(id)

    def __iter__(self):
        for modifiers in self.attachments.values():
            for modifier in modifiers:
                yield modifier

    def calculate(self):
        # Modifier rule:
        #   1. all * and / are applied cumulatively to the raw value;
        #   2. then all + and - are applied to that result;
        #   3. if any = exists, the final value is the last added = value.
        value = self.raw

        for modifier in self:
            op = modifier['operation']
            if op in ('*', '/'):
                value = MODIFIERS[op](value, modifier['value'])

        equals = []
        for modifier in self:
            op = modifier['operation']
            if op in ('+', '-'):
                value = MODIFIERS[op](value, modifier['value'])
            elif op == '=':
                equals.append(modifier)

        if equals:
            return equals[-1]['value']
        return value


MODIFIERS = {
    '+': lambda v, opt: v + opt,
    '-': lambda v, opt: v - opt,
    '*': lambda v, opt: v * opt,
    '/': lambda v, opt: v / opt,
    '=': lambda _, opt: opt,
}


class GunBasic(object):

    firingDuration = 0
    shootSpread = 0
    attachments = {}
    attachmentCache = {}
    categories = {} # type: dict[str, ModifierCategory]


    def __init__(self, asset, ammoCount=None):
        # type: (Asset, int | None) -> None
        level = LevelClient.getInstance()
        self.cam = level.camera
        self.audio = level.customAudio
        self.animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)
        self.vfxSystem = PlayerShooterVfxSystem.getInstance()
        self.bulletSystem = ClientBulletSystem.getInstance()
        self.featureComponent = getOrCreateSingletonComponent(LocalFeaturesComponent)
        self.resetTo(asset, ammoCount)


    def _createModifierCatIfAbsent(self, stat, raw):
        cat = ModifierCategory(stat, raw)
        self.categories[stat] = cat


    def _applyServerData(self, data):
        self.bulletCount = data['ammoCount']
        self.attachments = data['attachments']


    def setAmmoChangeCallback(self, callback):
        # type: (object) -> None
        self._onAmmoChanged = callback

    def _notifyAmmoChanged(self):
        if self._onAmmoChanged:
            self._onAmmoChanged(self.bulletCount)


    def removeAttachment(self, slot):
        slotId = slot['slotId']
        self.vfxSystem.transitionToCamera('camera', 0.2)
        self.attachments.pop(slotId, None)

        # Drop attachment cache entries that are no longer installed.
        installed = set(self.attachments.values())
        for cachedId in list(self.attachmentCache):
            if cachedId not in installed:
                self.attachmentCache.pop(cachedId, None)

        # Rebuild from the current attachment map only.
        self._rebuildModifierCategories()
        self._rebuildFeatures()


    def _rebuildFeatures(self):
        # Rebuild feature state from the base weapon plus current attachments.
        # This prevents stale features (e.g. bayonet) surviving after removal.
        self.featureComponent.clear()
        self.featureComponent.applyFromDict(self.asset['features'])
        for attachmentId in self.attachments.values():
            asset = self.attachmentCache.get(attachmentId)
            if asset is None:
                asset = self._findAttachmentAsset(attachmentId)
            if asset:
                self._updateAttachmentFeatures(asset)

    def _rebuildModifierCategories(self):
        self.categories = {}
        for attachmentId in self.attachments.values():
            asset = self.attachmentCache.get(attachmentId)
            if asset is None:
                asset = self._findAttachmentAsset(attachmentId)
            if not asset:
                continue
            for modifier in asset.get('modifiers', []):
                stat = modifier.get('stat')
                if stat and stat not in self.categories:
                    self.modify(stat)
            for cat in self.categories.values():
                cat.applyAttachment(asset)

    def applyAttachment(self, slot, attachment):
        if attachment == None:
            self.removeAttachment(slot)
            self._handleAttachmentVisual(slot, attachment)
            return
        attachmentId = attachment['attachmentId']
        slotId = slot['slotId']
        existingId = self.attachments.get(slotId)
        if existingId and existingId != attachmentId:
            self.removeAttachment(slot)
        self.attachments[slotId] = attachmentId
        self.attachmentCache[attachmentId] = attachment
        self._rebuildModifierCategories()
        self._rebuildFeatures()
        self._handleAttachmentVisual(slot, attachment)
        self.vfxSystem.transitionToCamera(slot['cameraAligned'], 0.2)


    def _findAttachmentAsset(self, attachmentId):
        # type: (str) -> dict | None
        try:
            names = dir(Asset.reach('attachments', True))
        except Exception:
            return None
        for name in names:
            if name.startswith('__'):
                continue
            try:
                asset = Asset('attachments.' + name).load(True)
            except Exception:
                asset = None
            if asset and asset.get('attachmentId') == attachmentId:
                return asset
            # Subpackage: attachments.appearance.*
            try:
                subNames = dir(Asset.reach('attachments.' + name, True))
            except Exception:
                subNames = []
            for sub in subNames:
                if sub.startswith('__'):
                    continue
                try:
                    subAsset = Asset('attachments.' + name + '.' + sub).load(True)
                except Exception:
                    continue
                if subAsset and subAsset.get('attachmentId') == attachmentId:
                    return subAsset
        return None

    def applyServerAttachments(self, attachments):
        # type: (dict) -> None
        """Apply a server-authoritative attachment map to this weapon."""
        if not isinstance(attachments, dict):
            attachments = {}
        installed = dict(self.attachments)
        for slot in self.slots:
            slotId = slot['slotId']
            if slotId in installed and slotId not in attachments:
                self.removeAttachment(slot)

        for slot in self.slots:
            slotId = slot['slotId']
            attachmentId = attachments.get(slotId)
            if not attachmentId:
                continue
            if self.attachments.get(slotId) == attachmentId:
                continue
            asset = self._findAttachmentAsset(attachmentId)
            if asset:
                self.applyAttachment(slot, asset)

    def _updateAttachmentFeatures(self, attachment, remove=False):
        if remove:
            restoreList = attachment.get('-features', [])
            for shouldRestore in restoreList:
                self.featureComponent.enableFeature(shouldRestore)

            shouldDiscards = attachment.get('+features', [])
            for discard in shouldDiscards:
                fName = discard if type(discard) == str else discard['name']
                self.featureComponent.discardFeature(fName)
            return
        discradedList = attachment.get('-features', [])
        for shouldDiscard in discradedList:
            self.featureComponent.discardFeature(shouldDiscard)
        shouldAppends = attachment.get('+features', [])
        for append in shouldAppends:
            appendIsStr = type(append) == str
            fName = append if appendIsStr else append['name']
            fParams = {} if appendIsStr else append['params']
            self.featureComponent.applyFeature(fName, fParams)


    def _handleAttachmentVisual(self, slot, attachment):
        if slot['type'] == 'baked':
            self._setBakedAttachmentEnabled(slot, bool(attachment))
            return
        

    def _setBakedAttachmentEnabled(self, slot, enabled):
        controlName = slot.get('control')
        if not controlName:
            return
        NamedEntityVariable(
            localPlayerId(),
            controlName,
        ).setValue(int(enabled))


    @Async
    def resetTo(self, asset, ammoCount=None):
        # type: (Asset, int | None) -> None
        asset = asset.duplicated()
        self.asset = asset
        self.categories = {}
        self.bolt = asset['bolt']
        self.trigger = asset['trigger']
        self.feed = asset['feed']
        self.barrel = asset['barrel']
        self.handling = asset['handling']
        self.featureComponent.clear()
        self.featureComponent.applyFromDict(asset['features'])
        self.slots = asset['slots']
        self.attachments = {}
        self.attachmentCache = {}
        for slot in self.slots:
            if slot.get('type') == 'baked':
                self._setBakedAttachmentEnabled(slot, False)
        self.boltCycleMode = self.bolt['cycleMode']
        self.isFullAuto = self.trigger.get('isFullAuto')

        capacity = self.modify(stats.magazineCapacity)
        if ammoCount is None or ammoCount < 0:
            self.bulletCount = capacity
        else:
            self.bulletCount = max(0, min(capacity, int(ammoCount)))
        self.bullet = None
        self.firedCase = False
        self._onAmmoChanged = None
        self.boltOpend = False
        self.pressingTrigger = False
        self.isFiring = False
        self.actionToken = 0
        self.boltCloseTimer = None
        self.curState = GunState.Hold
        self.aiming = False
        self.reloadTimer = None
        self.reloadToken = 0
        self.reloadAnimKey = None
        self.reloadBuffered = False
        self.fireBuffered = False
        self.canCycle = True
        self.safe = False
        self.autoMode = self.bolt['disconnector'] in ('enable', 'switch') and GunAutoState.Semi or GunAutoState.Full
        self.nextFireTime = 0
        self.autoFireInterval = self.bolt['boltOpenTime'] + self.bolt['boltCloseTime']
        self.stun = None

    def modify(self, stat, pathTo=None, default=0):
        if not pathTo:
            pathTo = getattr(StatMapping, stat)

        if stat not in self.categories:
            raw = dictx.visit(self.asset, pathTo)
            self._createModifierCatIfAbsent(stat, raw)
            return raw if raw != None else default

        category = self.categories[stat]
        return category.calculate()

    @Async
    def wait(self, sec):
        ftr = wait(sec)
        self.stun = ftr
        yield ftr
        self.stun = None


    def isManuallyCyclingBolt(self):
        return self.boltCycleMode == 'manual' and self.curState == GunState.Cycling


    def isWaiting(self):
        return self.stun is not None


    def changeSafeState(self, bool=True):
        if self.curState == GunState.Hold:
            self.safe = bool


    def changeAutoMode(self, autoMode):
        disconnector = self.bolt['disconnector']
        if disconnector == 'switch':
            self.autoMode = autoMode
            return autoMode

        if disconnector == 'none':
            self.autoMode = GunAutoState.Full
            return GunAutoState.Full
        
        if disconnector == 'enable':
            self.autoMode = GunAutoState.Semi
            return GunAutoState.Semi


    def canOperate(self):
        return self.curState not in (GunState.Firing, GunState.Cycling) and not self.isWaiting()
    

    def canReload(self):
        return self.curState == GunState.Hold and not self.isWaiting()


    def applyBullet(self, uri):
        if not self.canOperate():
            return
        if uri in self.feed['ammoType']:
            self.bullet = Asset(uri).load(True)
            self.curState = GunState.Hold
            if not self.bolt:
                raise ValueError('Bullet should not be "None"')


    def changeFullAuto(self, fullAuto=True):
        if not self.canOperate():
            return
        self.isFullAuto = fullAuto
        self.curState = GunState.Hold


    @Async
    def pressTrigger(self):
        if not self.canOperate() or self.safe:
            return
        token = self.actionToken

        if self.trigger['fireMode'] != 'burst':
            if self.bulletCount <= 0:
                # 子弹打空后左键只播空仓/空膛音
                self.tryFireBullet()
                return
            # firedCase 检测栓动/泵动有没有退空弹
            # boltOpend 检测是不是空挂
            if self.firedCase or self.boltOpend:
                self.cycleBolt()
                return
            self.isFiring = True
            self.curState = GunState.Firing
            yield self.wait(self.modify(stats.triggerDelay))
            if token != self.actionToken:
                return
            self.pressingTrigger = True
            self.tryFireBullet()
            self.curState = GunState.Hold
            return

        self.pressingTrigger = True
        self.isFiring = True
        burstCount = self.trigger.get('burstCount', 1)
        everySpan = self.modify(stats.triggerDelay) / burstCount
        for _ in range(burstCount):
            yield self.wait(everySpan)
            if token != self.actionToken:
                return
            self.tryFireBullet()
        self.isFiring = False
        self.curState = GunState.Hold


    def releaseTrigger(self):
        self.pressingTrigger = False
        self.nextFireTime = 0


    @Async
    def cycleBolt(self):
        """
        这里的manual指的是自动/半自动武器是否手动拉枪机
        """
        if self.curState in (GunState.Cycling, GunState.Reloading):
            return

        token = self.actionToken
        self.curState = GunState.Cycling
        animEx = self.animEx
        isManualCycle = self.bolt['cycleMode'] == 'manual'
        animLayer = isManualCycle and 'default' or 'bolt'

        if not self.boltOpend:
            animEx.play(
                self.bolt['boltOpenAnim'],
                animLayer
            )
            yield self.wait(self.bolt['boltOpenTime'])
            if token != self.actionToken:
                return
            self.boltOpend = True
            # 实际上子弹只会在枪机打开时抛出，不管子弹有没有被射击过
            self.dropCasing()

            # 拉栓过程中预输入了换弹：枪机一拉开就直接进入换弹，
            # 不要再闭锁后再拉开一次，避免浪费下一发。
            if self.reloadBuffered:
                self.reloadBuffered = False
                self.isFiring = False
                self.curState = GunState.Hold
                self.reload()
                return

        isEmpty = self.bulletCount <= 0
        if not isEmpty:
            # 在有余弹的时候才会退出空弹，因为在全部子弹都退出时枪内没有上膛的子弹
            self.firedCase = False

        if isEmpty and self.bolt['holdOpenOnEmpty']:
            # 允许空挂的时候不应该让枪机闭合
            self.isFiring = False
            self.curState = GunState.Hold
            if self.reloadBuffered and self.canReload():
                self.reloadBuffered = False
                self.reload()
            return

        animEx.play(
            self.bolt['boltCloseAnim'],
            animLayer
        )
        yield self.wait(self.bolt['boltCloseTime'])
        if token != self.actionToken:
            return
        self.boltOpend = False
        self.curState = GunState.Hold

        # 如果拉栓/闭锁过程中预输入了换弹，闭锁完成后进入换弹
        if self.reloadBuffered and self.canReload():
            self.reloadBuffered = False
            self.isFiring = False
            self.reload()
            return

        if not isManualCycle and not isEmpty        \
            and self.autoMode == GunAutoState.Full  \
            and self.pressingTrigger:
            now = time.time()
            if now < self.nextFireTime:
                yield self.wait(self.nextFireTime - now)
            if token != self.actionToken or not self.pressingTrigger:
                self.isFiring = False
                return
            self._fireBullet()
        else:
            self.isFiring = False


    @Async
    def tryFireBullet(self):
        if self.bulletCount <= 0:
            emptyFireSound = self.modify(stats.emptyFireSound)
            emptyFireSound and self.audio.PlayCustomUIMusic(emptyFireSound)
            return False
        self._fireBullet()
        return True


    SPREAD_FUNC = {
        'OneMinus': lambda s, x: 1 - math.exp(-s * x),
        'Native': lambda s, x: math.exp(-s * x)
    }


    def calcSpread(self):
        spreadConf = self.barrel['spread']
        strength = spreadConf['strength']
        maxSpread = spreadConf['maxSpread']
        minSpread = spreadConf['minSpread']
        dSpread = GunBasic.SPREAD_FUNC[spreadConf['fnType']](strength, self.firingDuration)
        scale = maxSpread - minSpread
        self.shootSpread = dSpread * scale + minSpread


    @Async
    def _fireBullet(self):
        # TODO: shoot bullet
        self.interruptReloading()
        self.isFiring = True
        token = self.actionToken
        spreadMul = self.aiming and self.modify(stats.spreadMultiplier, default=1) or 1
        self.vfxSystem.shootCamVfx(
            self.modify(stats.fireSound),
            (
                self.modify(stats.recoilX),
                self.modify(stats.recoilY),
            ),
        )
        self.bulletSystem.createBulletFromFacing(
            self.bullet, self.modify(stats.velocityModifier), self.vfxSystem.applySpreadOffset(spreadMul)
        )
        self.calcSpread()
        self.animEx.play(self.modify(stats.animShoot), replay=True, noBlending=True)
        self.firedCase = True

        # 自动武器用绝对时间累加下一发，避免多个 wait 被 tick 量化导致射速抖动
        if self.bolt['cycleMode'] != 'manual' and self.autoMode == GunAutoState.Full:
            now = time.time()
            if self.nextFireTime <= 0:
                self.nextFireTime = now + self.autoFireInterval
            else:
                self.nextFireTime += self.autoFireInterval

        if self.bolt['cycleMode'] == 'manual':
            yield self.wait(self.bolt['shootRestoreTime'])
            if token != self.actionToken:
                self.isFiring = False
                return
            if not self.canCycle:
                self.isFiring = False
                return

        self.cycleBolt()


    def findAmmoCountInInv(self, itemType):
        # TODO: 返回背包中具体的子弹数量
        return 50
    

    def consumeBullets(self, itemType, count):
        # TODO: 消耗count个子弹，但有可能背包没这么多子弹，所以消耗后返回具体消耗数量
        return count
    

    def fillBullet(self, itemType, count):
        consumed = self.consumeBullets(itemType, count)
        self.bulletCount += consumed
        self._notifyAmmoChanged()
        return consumed


    def interruptReloading(self):
        self.reloadToken += 1
        self.fireBuffered = False
        if self.reloadTimer:
            self.reloadTimer.cancel()
            self.reloadTimer = None
        if self.reloadAnimKey:
            self.animEx.stop(self.reloadAnimKey)
            self.reloadAnimKey = None
        self.canCycle = True
        if self.curState == GunState.Reloading:
            self.curState = GunState.Hold


    def cancelAll(self):
        # 取消旧武器所有异步协程/定时器，避免切枪后残留逻辑覆盖新武器 draw
        self.actionToken += 1
        self.interruptReloading()
        if self.boltCloseTimer:
            cancelTimer(self.boltCloseTimer)
            self.boltCloseTimer = None
        self.isFiring = False
        self.pressingTrigger = False
        self.stun = None
        self.curState = GunState.Hold


    def shouldUseCupPortBoltOpen(self):
        return not self.firedCase and self.bulletCount
    

    def dropCasing(self):
        self.firedCase = False
        if self.bulletCount > 0:
            self.bulletCount -= 1
            self._notifyAmmoChanged()
            self.vfxSystem.dropEmptyBullet(
                self.bullet['modelAsset']['casingEntity'],
                self.bolt['ejectVelocity']
            )


    @Async
    def reload(self):
        magazineCapacity = self.modify(stats.magazineCapacity)
        if self.bulletCount >= magazineCapacity or self.reloadTimer:
            return

        self.reloadToken += 1
        token = self.reloadToken
        self.reloadBuffered = False
        self.fireBuffered = False
        self.isFiring = False
        self.canCycle = False
        self.curState = GunState.Reloading
        count = 0
        bulletItemType = self.bullet.get('itemType')
        isManual = self.bolt['cycleMode'] == 'manual'

        for ammoAssetId in self.feed['ammoType']:
            ammoId = Asset(ammoAssetId).load(True)['itemType']
            if ammoId != bulletItemType:
                continue
            count = self.findAmmoCountInInv(ammoId)
            if count > 0:
                break
        if count <= 0:
            self.canCycle = True
            self.curState = GunState.Hold
            return

        reloadMode = self.findProperReloadMode()
        if not reloadMode:
            self.canCycle = True
            self.curState = GunState.Hold
            return

        if isManual and not self.boltOpend:
            shouldUseCupPortBoltOpen = self.shouldUseCupPortBoltOpen()
            self.animEx.play(
                shouldUseCupPortBoltOpen                \
                    and self.bolt['cuppedPortOpenBolt'] \
                    or self.bolt['boltOpenAnim'],
            )
            yield self.wait(
                shouldUseCupPortBoltOpen                \
                    and self.bolt['cuppedPortOpenTime'] \
                    or self.bolt['boltOpenTime']
            )
            if token != self.reloadToken:
                return
            self.boltOpend = True
            shouldUseCupPortBoltOpen or self.dropCasing()

        self.reloadAnimKey = reloadMode['animation']
        self.animEx.play(reloadMode['animation'], replay=True)

        def doReload():
            if token != self.reloadToken:
                return
            if self.reloadTimer:
                self.reloadTimer.cancel()
                self.reloadTimer = None
            self.reloadAnimKey = None

            reloadType = reloadMode['reloadType']
            remains = count - self.fillBullet(
                bulletItemType,
                reloadType == 'replace' and magazineCapacity - self.bulletCount\
                    or reloadType == 'add' and 1 or reloadMode['countPerClip']
            )
            self.canCycle = True

            # 玩家预输入了射击：装完当前这个阶段就打断后续装填
            if self.fireBuffered and isManual:
                self.fireBuffered = False
                if self.boltOpend:
                    def restoreBolt():
                        self.fireBuffered = False
                        self.boltOpend = False
                        self.firedCase = False
                        self.curState = GunState.Hold
                    self.animEx.play(self.bolt['boltCloseAnim'], isManual and 'default' or 'bolt')
                    self.boltCloseTimer = addTimer(self.bolt['boltCloseTime'], restoreBolt, False)
                else:
                    self.curState = GunState.Hold
                return

            if self.bulletCount < magazineCapacity and remains > 0:
                self.reload()
                return

            if self.boltOpend:
                def restoreBolt():
                    self.boltOpend = False
                    self.firedCase = False
                    self.curState = GunState.Hold

                self.animEx.play(self.bolt['boltCloseAnim'], isManual and 'default' or 'bolt')
                self.boltCloseTimer = addTimer(self.bolt['boltCloseTime'], restoreBolt, False)
            else:
                self.curState = GunState.Hold

        self.reloadTimer = TimerAdapter(reloadMode['reloadTime'], doReload, False)
        self.reloadTimer.start()


    def findProperReloadMode(self):
        remains = self.bulletCount
        capacity = self.modify(stats.magazineCapacity)
        for mode in self.feed['reloadModes']:
            condition = mode['condition']
            if remains == 0 and condition == 'empty':
                return mode
            if 0 < remains < capacity and condition == 'not_full':
                return mode
            if condition == 'clip_available':
                countPerClip = mode['countPerClip']
                if capacity - remains >= countPerClip and capacity > countPerClip:
                    return mode
        return None

