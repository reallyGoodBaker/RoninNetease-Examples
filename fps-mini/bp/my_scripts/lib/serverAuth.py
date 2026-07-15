from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    Remote, compServer, LevelServer,
)


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