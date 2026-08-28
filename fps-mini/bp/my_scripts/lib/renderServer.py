from ..engine.architect.compact import (
    SubsystemServer, ServerSubsystem,
    CustomEvent,
)


@SubsystemServer
class RenderServerSystem(ServerSubsystem):

    PlayerRenderUriMapping = {}

    @CustomEvent('renderResource')
    def onPlayerChangeRenderRes(self, ev):
        RenderServerSystem.PlayerRenderUriMapping[ev.entity] = ev.uri
        self.sendAllClients('syncResource', ev.dict())

    @CustomEvent('requestResource')
    def onPlayerRequest(self, ev):
        uri = RenderServerSystem.PlayerRenderUriMapping[ev.entity]
        if uri:
            self.sendClient(ev.client, 'syncResource', {
                'entity': ev.entity,
                'uri': uri
            })