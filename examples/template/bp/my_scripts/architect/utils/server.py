from ..level.server import LevelServer, compServer
from mod.common.minecraftEnum import EntityType
from ..core.export import ServerSubsystem, SubsystemServer

def isPlayer(entityId):
    return compServer.CreateEngineType(entityId).GetEngineType() == EntityType.Player

def runCommand(cmd, entityId):
    return LevelServer.command.SetCommand(cmd, entityId)

def motion(entityId, mot, ignoreTypes=[]):
    typeComp = compServer.CreateEngineType(entityId)
    typeStr = typeComp.GetEngineTypeStr()
    if typeStr in ignoreTypes:
        return
    if typeComp.GetEngineType() == EntityType.Player:
        return compServer.CreateActorMotion(entityId).SetPlayerMotion(mot)
    else:
        return compServer.CreateActorMotion(entityId).SetMotion(mot)
    
def sound(entityId, sound):
    return LevelServer.command.SetCommand('playsound {} @a ~~1~ 2'.format(sound), entityId)

def particle(particle, pos):
    x, y, z = pos
    return LevelServer.command.SetCommand('particle {} {} {} {}'.format(particle, x, y, z))

def soundServer(entityId, sound):
    utilsServer = ServerUtilsSubsys.getInstance() # type: ignore
    utilsServer.playSound(entityId, sound) # type: ignore

def soundStopServer(entityId, sound):
    utilsServer = ServerUtilsSubsys.getInstance() # type: ignore
    utilsServer.stopSound(entityId, sound) # type: ignore

@SubsystemServer
class ServerUtilsSubsys(ServerSubsystem):

    def playSound(self, entityId, sound):
        self.sendAllClients('PlayCustomAudio', {
            'entityId': entityId,
            'sound': sound
        })

    def stopSound(self, entityId, sound):
        self.sendAllClients('StopCustomAudio', {
            'entityId': entityId,
            'sound': sound
        })