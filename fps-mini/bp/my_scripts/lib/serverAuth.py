from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    Remote, compServer, LevelServer,
    EventListener, events,
    Component, BaseCompServer,
    getOrCreateComponent,
    Sched, Query,
)
from mod.common.minecraftEnum import AttrType, AttributeModifierOperation, AttributeOperands
from ..engine.architect.math.double import clamp


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

    @Remote
    def tryDamageEntity(self, playerId, target, damage, caliber):
        hurtComp = compServer.CreateHurt(target)
        hurtComp.Hurt(damage, 'custom', playerId, knocked=False, customTag=caliber)

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

    @Remote
    def enablePlayerSprinting(self, playerId, enabled):
        attr = compServer.CreateAttr(playerId)
        if enabled:
            attr.RemoveModifier(
                AttrType.SPEED,
                'fps:speed_modifier',
            )
        else:
            attr.AddModifier(
                AttrType.SPEED,
                'fps:speed_modifier',
                0.8,
                AttributeModifierOperation.OperationMultiplyTotal,
                AttributeOperands.OperandCurrent,
            )