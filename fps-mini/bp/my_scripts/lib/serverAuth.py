from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    Remote, compServer, LevelServer,
)
from mod.common.minecraftEnum import AttrType, AttributeModifierOperation, AttributeOperands


@SubsystemServer
class BulletServerAuthSystem(ServerSubsystem):

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