from ..engine.architect.compact import (
    localPlayerId, compClient,
    Component, getOrCreateComponent, BaseCompClient,
    getOneComponent,
    SubsystemClient, ClientSubsystem,
    Asset,
    CustomEvent, EventListener, events,
    getBonePosition,
)

from ..engine.architect.plugins.animation.components.animClient import AnimationExComponent
from ..assets.animMeta import AnimMeta

# TODO: Remove these imports
from mod.client.component.actorRenderCompClient import ActorRenderCompClient

FP_COND = 'v.is_first_person && !q.is_spectator'
TP_COND = '!v.is_first_person && !v.map_face_icon && !q.is_spectator'

# Appearance/tint may override the weapon's default tint mask at runtime.
_tintMaskOverride = {}


def setPlayerTintMaskTexture(entityId, texturePath):
    # type: (str, str) -> None
    """Override the tint_mask texture for the next applyRenderResource().

    We intentionally do not touch the live renderer here: rebuilding the
    player render at the wrong time can disturb the already-working weapon
    render. The override is picked up on the next render-resource apply.
    """
    if not entityId or not texturePath:
        return
    _tintMaskOverride[entityId] = texturePath


def setNativeRenderControllerEnabled(renderer, enable=True):
    # type: (ActorRenderCompClient, bool) -> None
    if enable:
        renderer.AddPlayerRenderController('controller.render.player.first_person', FP_COND)
        renderer.AddPlayerRenderController('controller.render.player.third_person', TP_COND)
    else:
        renderer.RemovePlayerRenderController('controller.render.player.first_person')
        renderer.RemovePlayerRenderController('controller.render.player.third_person')


def setNativeRootAnimationEnabled(renderer, enabled=True):
    # type: (ActorRenderCompClient, bool) -> None
    if enabled:
        renderer.AddPlayerScriptAnimate('root', autoReplace=True)
    else:
        renderer.AddPlayerScriptAnimate('root', '0', True)


def findResource(entityId, renderer, resType, key):
    # type: (str, ActorRenderCompClient, str, str) -> None
    keys = renderer.GetActorRenderParams(entityId, resType)
    if not keys or key not in keys:
        return None
    index = keys.index(key)    
    return renderer.GetActorRenderParams(entityId, resType, True)[index]


@Component()
class LocalPlayerRenderParams(BaseCompClient):
    geometry = None
    first = []
    third = []

    def onCreate(self, entityId):
        self.entityId = entityId

    def reset(self):
        self.geometry = None
        self.first = []
        self.third = []


def applyRenderResource(renderer, asset, renderParams):
    # type: (ActorRenderCompClient, dict, LocalPlayerRenderParams) -> None
    setNativeRenderControllerEnabled(renderer, False)
    setNativeRootAnimationEnabled(renderer, False)

    if not renderParams.geometry:
        renderParams.geometry = findResource(renderParams.entityId, renderer, 'geometry', 'default')
        renderer.AddPlayerGeometry('player', renderParams.geometry)

    # 网易的bug，如果不删除某个组并重新添加，它会导致某个组的粒子绑定出问题
    renderer.AddPlayerGeometry('default', renderParams.geometry)
    renderer.RebuildPlayerRender()

    renderer.AddPlayerGeometry('default', asset['model'])
    renderer.AddPlayerGeometry('third_model', asset['third_model'])
    renderer.AddPlayerGeometry('arms', asset['arms'])
    for k, v in asset['materials'].items():
        renderer.AddPlayerRenderMaterial(k, v)
    renderer.AddPlayerTexture('weapon', asset['texture'])
    tintMaskTexture = _tintMaskOverride.get(renderParams.entityId) or asset.get('tintMaskTexture') or 'textures/entity/weapons/bolt_tint_mask'
    renderer.AddPlayerTexture('tint_mask', tintMaskTexture)
    first = asset['render']['first_person']
    third = asset['render']['third_person']
    renderParams.first = first
    renderParams.third = third
    for renderController in first:
        renderer.AddPlayerRenderController(renderController, FP_COND)
    for renderController in third:
        renderer.AddPlayerRenderController(renderController, TP_COND)

    renderer.AddPlayerAnimation('custom.base', 'animation.custom.weapons.root')
    renderer.AddPlayerAnimation('custom.walk', 'animation.custom.humanoid.walk')
    renderer.AddPlayerAnimation('custom.hold', 'animation.custom.humanoid.hold')
    renderer.AddPlayerAnimation('custom.aiming', 'animation.custom.humanoid.aiming')
    renderer.AddPlayerAnimation('custom.riding', 'animation.custom.humanoid.riding')
    renderer.AddPlayerAnimationController('custom.root', 'controller.animation.custom_root')
    renderer.AddPlayerScriptAnimate('custom.root', autoReplace=True)

    renderer.RebuildPlayerRender()


def resetRenderResource(renderer, renderParams):
    # type: (ActorRenderCompClient, LocalPlayerRenderParams) -> None
    _tintMaskOverride.pop(renderParams.entityId, None)
    if not renderParams.geometry:
        renderer.AddPlayerGeometry('default', 'geometry.humanoid.custom')
    else:
        renderer.AddPlayerGeometry('default', renderParams.geometry)
    renderer.AddPlayerScriptAnimate('custom.root', '0', True)
    for renderController in renderParams.first:
        renderer.RemovePlayerRenderController(renderController)
    for renderController in renderParams.third:
        renderer.RemovePlayerRenderController(renderController)

    setNativeRenderControllerEnabled(renderer)
    setNativeRootAnimationEnabled(renderer)

    renderer.RebuildPlayerRender()




def registerWeaponAnimations(entityId, weaponName):
    # type: (str, str) -> None
    animEx = getOrCreateComponent(entityId, AnimationExComponent)
    animEx.registerMetadatas(AnimMeta)
    animEx.clearRegisteredAnimations()
    animEx.registerAnimations(Asset('animations.' + weaponName).load(True))
    for name, easingDef in Asset('easings.' + weaponName).load(True).items():
        animEx.registerEasing(name, easingDef)
    animEx.updateActorAnimDef()


def clearWeaponAnimations(entityId):
    # type: (str) -> None
    animEx = getOneComponent(entityId, AnimationExComponent)
    if animEx:
        animEx.clearRegisteredAnimations()
        animEx.updateActorAnimDef()


@SubsystemClient
class WeaponRenderSystem(ClientSubsystem):

    WeaponMapping = {}

    @classmethod
    def registerAssetMapping(cls, mapping):
        for k, v in mapping.items():
            cls.WeaponMapping[k] = v


    def initPlayerRender(self, entityId):
        localId = localPlayerId()
        if entityId != localId:
            self.sendServer('requestResource', { 'entity': entityId, 'client': localId })
            return

        item = compClient.CreateItem(entityId).GetCarriedItem()
        if not item:
            self.sendServer('renderResource', { 'entity': entityId, 'uri': None })
            return
        assetUri = WeaponRenderSystem.WeaponMapping.get(item['newItemName'])
        self.sendServer('renderResource', { 'entity': entityId, 'uri': assetUri })


    def changeRenderResource(self, entity, assetUri):
        renderer = compClient.CreateActorRender(entity)
        if not assetUri:
            if entity != localPlayerId():
                clearWeaponAnimations(entity)
            renderParams = getOneComponent(entity, LocalPlayerRenderParams)
            if not renderParams:
                return
            resetRenderResource(renderer, renderParams)
            renderParams.reset()
            return

        applyRenderResource(
            renderer,
            Asset('renderResources.' + assetUri).load(True),
            getOrCreateComponent(entity, LocalPlayerRenderParams)
        )
        if entity != localPlayerId():
            registerWeaponAnimations(entity, assetUri)
        # 网易bug，切换模型后需要手动绑定一次粒子，
        # 不然之后第一次获取得到的结果一定是错的
        getBonePosition(entity, 'muzzle')


    @EventListener()
    def onPlayerCreated(self, ev=events.AddPlayerCreatedClientEvent()):
        self.initPlayerRender(ev.playerId)


    @EventListener()
    def onChangeCarriedItem(self, _=events.OnCarriedNewItemChangedClientEvent()):
        # Render resource change is driven by ShooterSystem after holster animation.
        pass


    @CustomEvent('syncResource')
    def onSyncRenderResource(self, ev):
        self.changeRenderResource(ev.entity, ev.uri)