from .engine.architect.compact import *

@SubsystemServer
class AnimPlayerServer(ServerSubsystem):
    @Remote
    def cameraShake(self, playerId):
        runCommand('camerashake add @s 0.4 0.1 positional'.format(playerId), playerId)

    @Remote
    def doAttack(self, playerId, entities, damage):
        for entityId in entities:
            compServer.CreateHurt(entityId).Hurt(damage, 'entity_attack', playerId)