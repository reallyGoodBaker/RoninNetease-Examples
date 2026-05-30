from ..core.export import ClientSubsystem, SubsystemClient
from ..event import EventListener
from ..level.client import LevelClient, compClient
from mod.common.minecraftEnum import EntityType

def isPlayer(entityId):
    return compClient.CreateEngineType(entityId).GetEngineType() == EntityType.Player

@SubsystemClient
class ClientUtilsSubsys(ClientSubsystem):

    def onInit(self):
        self.level = LevelClient.getInstance()

    @EventListener('PlayCustomAudio', isCustomEvent=True)
    def playSound(self, ev):
        entityId = ev.entityId
        entityPos = compClient.CreatePos(entityId).GetPos()
        self.level.customAudio.PlayCustomMusic(ev.sound, entityPos)

    @EventListener('StopCustomAudio', isCustomEvent=True)
    def stopSound(self, ev):
        self.level.customAudio.StopCustomMusic(ev.sound, 0.1)