from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    Remote, compServer, LevelServer,
    EventListener, events,
    Component, BaseCompServer,
    getOrCreateComponent,
    Sched, Query,
    SubsystemManager,
)
from mod.common.minecraftEnum import AttrType
from ..engine.architect.math.double import clamp
from ..engine.architect.persistent.server import ServerKVDatabase
from .gunSync import defaultGunStorage


def getOrCreateGunStorage(gunId, itemName=''):
    # type: (str, str) -> object
    """Return the GunStorage DatabaseView and ensure the gun record exists.

    The caller can use view.cache[gunId] to read and view.set(gunId, record)
    to persist the whole record back.
    """
    gunStorage = ServerKVDatabase.getInstance().createView('GunStorage')
    record = gunStorage.cache.get(gunId)
    if not isinstance(record, dict):
        gunStorage.set(gunId, defaultGunStorage(itemName))
    return gunStorage


@Component()
class HurtCDComp(BaseCompServer):
    remains = 0


@SubsystemServer
class BulletServerAuthSystem(ServerSubsystem):

    def onReady(self):
        LevelServer.game.SetHurtCD(0)

    @Remote
    def tryBreakBlock(self, playerId, pos):
        dimId = compServer.CreateDimension(playerId).GetEntityDimensionId()
        LevelServer.blockInfo.SetBlockNew(pos, {
            'name': 'minecraft:air'
        }, 0, dimId)

    @EventListener()
    def preventDamageInHurtCD(self, ev=events.DamageEvent()):
        if ev.cause != 'custom':
            hurt = getOrCreateComponent(ev.entityId, HurtCDComp)
            if hurt.remains == 0:
                hurt.remains = 15
                return
            ev.setEvent('damage', 0)

    @Sched.Tick()
    @Query(HurtCDComp)
    def decreaseHurtCD(self, hurt):
        # type: (HurtCDComp) -> None
        hurt.remains = clamp(hurt.remains - 1, 0, 9)

    def submitDamage(self, target, source, damage, caliber):
        hurtComp = compServer.CreateHurt(target)
        hurtComp.Hurt(damage, 'custom', source, knocked=False, customTag=caliber)

    @Remote
    def tryDamageEntity(self, playerId, target, damage, isHeadShot, caliber):
        attrComp = compServer.CreateAttr(target)
        remainss = attrComp.GetAttrValue(AttrType.HEALTH)
        willKill = damage >= remainss
        self.submitDamage(target, playerId, damage, caliber)
        SubsystemManager.getInstance().bus.execute(
            'ShooterIndicatorServer.hit',
            playerId, isHeadShot, willKill, target, damage
        )

