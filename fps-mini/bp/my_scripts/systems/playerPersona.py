from ..engine.architect.utils.persona.client import PersonaRendererComponent, HandItemVisibility
from ..engine.architect.compact import (
    localPlayerId, LevelClient,
    ClientSubsystem, SubsystemClient,
    clientApi,
    events, EventListener,
    getOrCreateComponent,
    QueryVariable,
    Asset,
)

WeaponAssetMapping = {
    'roninexample:pistol':  Asset('weapons.pistol'),
    'roninexample:bolt':    Asset('weapons.bolt'),
}

isFirstPerson = QueryVariable('is_first_person')

@SubsystemClient
class PlayerPersonaSystem(ClientSubsystem):

    def onInit(self):
        self.level = LevelClient.getInstance()

    def resetPlayerRenderResource(self, playerId):
        renderer = getOrCreateComponent(playerId, PersonaRendererComponent) # type: PersonaRendererComponent
        renderer.resetPlayerRenderConf()
        renderer.restorePlayerRootAnim()
        renderer.showHand(HandItemVisibility.All)
        clientApi.HideCrossHairGUI(False)

    def replacePlayerWeaponAsset(self, playerId, asset):
        renderer = getOrCreateComponent(playerId, PersonaRendererComponent) # type: PersonaRendererComponent
        renderer.showHand(HandItemVisibility.OnlyFirstPerson)
        renderer.shadowPlayerRootAnim('root_rot')
        renderer.changeRenderConf(asset.load(True), True)
        clientApi.HideCrossHairGUI(True)

    @EventListener()
    def onCarriedItemChanged(self, ev=events.OnCarriedNewItemChangedClientEvent()):
        itemName = ev.itemDict['newItemName']
        asset = WeaponAssetMapping.get(itemName)
        if asset:
            self.replacePlayerWeaponAsset(localPlayerId(), asset)
            self.broadcast('PlayerHoldNewWeapon', { 'itemName': itemName })
            return
        self.resetPlayerRenderResource(localPlayerId())

    @EventListener()
    def onLocalLoaded(self, _=events.OnLocalPlayerStopLoading()):
        isFirstPerson.setValue(localPlayerId(), self.level.playerView.GetPerspective() == 0)

    @EventListener()
    def onPerspChange(self, ev=events.PerspChangeClientEvent()):
        isFirstPerson.setValue(localPlayerId(), ev.to == 0)
