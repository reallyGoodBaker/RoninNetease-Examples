from ...core.export import ServerSubsystem, SubsystemServer
from ...event import EventListener
from ...core.basic import serverApi
from ..enhance.list import remove

@SubsystemServer
class PersonaServer(ServerSubsystem):

    def changePersona(self, id, renderConf):
        self.sendAllClients('PersonaChangeServer', {
            'id': id,
            'data': renderConf
        })

    def resetPersona(self, id):
        self.sendAllClients('PersonaResetServer', {
            'id': id,
        })

    _PersonaChanged = {}

    @EventListener('BroadcastPersonaChange', isCustomEvent=True)
    def onPersonaChangeClient(self, ev):
        PersonaServer._PersonaChanged[ev.id] = ev.data
        players = serverApi.GetPlayerList()
        remove(players, ev.__id__)
        self.sendClient(players, 'PersonaChangeClientAuthed', {
            'id': ev.id,
            'data': ev.data,
        })

    @EventListener('BroadcastPersonaReset', isCustomEvent=True)
    def onPersonaResetClient(self, ev):
        del PersonaServer._PersonaChanged[ev.id]
        players = serverApi.GetPlayerList()
        remove(players, ev.__id__)
        self.sendClient(players, 'PersonaResetClientAuthed', {
            'id': ev.id,
        })

    @EventListener('PersonaChangeClientInit', isCustomEvent=True)
    def onPersonaChangeClientInit(self, ev):
        instigator = ev.__id__
        for id, data in PersonaServer._PersonaChanged.items():
            self.sendClient(instigator, 'PersonaChangeClientAuthed', {
                'id': id,
                'data': data,
            })