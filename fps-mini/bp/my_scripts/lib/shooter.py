# -*- coding: utf-8 -*-
import copy

from ..engine.architect.compact import (
    Asset, Async, wait, Future, localPlayerId,
    LevelClient, getOrCreateComponent,
)
from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent


class ShooterState:
    Hold = 0
    BoltOpen = 1
    BoltClose = 2
    Reload = 3


class ShooterBasic(object):

    def __init__(self, source):
        asset = copy.deepcopy(source)
        level = LevelClient.getInstance()
        self.cam = level.camera
        self.audio = level.customAudio
        self.animEx = getOrCreateComponent(localPlayerId(), AnimationExComponent)

        self.bolt = asset['asset']
        self.trigger = asset['trigger']
        self.feed = asset['feed']
        self.barrel = asset['barrel']
        self.handling = asset['handling']
        self.features = asset['features']
        self.slots = asset['slots']
        self.extra = asset['extra']
        self.boltCycleMode = self.bolt['cycleMode']
        self.isFullAuto = self.trigger['isFullAuto']

        self.recoilX, self.recoilY = self.bolt['recoil']
        self.triggerDelay = self.trigger['delay']
        self.magazineCapacity = self.feed['magazineCapacity']
        self.velocityModifier = self.barrel['velocityModifier']
        self.maxSpread = self.barrel['maxSpread']
        self.spreadIncreasePerShot = self.barrel['spreadIncreasePerShot']
        self.speedModifier = self.handling['speedModifier']
        self.adsInTime = self.handling['adsInTime']
        self.adsOutTime = self.handling['adsOutTime']
        self.sprintToFireTime = self.handling['sprintToFireTime']

        self.bulletCount = 0
        self.attachments = {}
        self.bullet = None
        self.emptyBullet = False
        self.boldOpend = False
        self.pressingTrigger = False
        self.curState = ShooterState.Hold


    def applyBullet(self, uri):
        if uri in self.feed['ammoType']:
            self.bullet = Asset(uri).load(True)


    def changeFullAuto(self, fullAuto=True):
        self.isFullAuto = fullAuto


    @Async
    def pressTrigger(self):
        if self.trigger['fireMode'] != 'burst':
            yield wait(self.triggerDelay)
            self.tryFireBullet()
            return

        burstCount = self.trigger.get('burstCount', 1)
        everySpan = self.triggerDelay / burstCount
        for _ in range(burstCount):
            yield wait(everySpan)
            self.tryFireBullet()


    def releaseTrigger(self):
        self.pressingTrigger = False


    @Async
    def manualCycleBolt(self):
        self.boldOpend = True
        animEx = self.animEx
        if self.bolt['cycleMode'] == 'manual':
            animEx.play(self.bolt['manualCycleAnim'])
            yield wait(self.bolt['cycleTime'])
            self.emptyBullet = False
            self.boldOpend = False
            return
        animEx.play(self.bolt['cycleOpenAnim'], clientOnly=True)
        yield wait(self.bolt['autoCycleOpenTime'])
        self.emptyBullet = False
        animEx.play(self.bolt['cycleCloseAnim'], clientOnly=True)
        yield wait(self.bolt['autoCycleOpenTime'])
        self.boldOpend = False


    def tryFireBullet(self):
        if self.bulletCount <= 0:
            emptyFireSound = self.bolt['emptyFireSound']
            emptyFireSound and self.audio.PlayCustomUIMusic(emptyFireSound)
            return False 
        if self.emptyBullet or self.boldOpend:
            self.manualCycleBolt()
            return False
        self._fireBullet()
        return True


    @Async
    def _fireBullet(self):
        # TODO: shoot bullet
        animEx = self.animEx
        self.bulletCount -= 1
        self.emptyBullet = True

        if self.bolt['cycleMode'] == 'manual' and self.bulletCount > 0:
            self.manualCycleBolt()
            return

        animEx.play(self.bolt['cycleOpenAnim'], clientOnly=True)
        yield wait(self.bolt['autoCycleOpenTime'])

        if not self.bolt['holdOpenOnEmpty'] or self.bulletCount > 0:
            animEx.play(self.bolt['cycleCloseAnim'], clientOnly=True)
            yield wait(self.bolt['autoCycleOpenTime'])
            self.boldOpend = False