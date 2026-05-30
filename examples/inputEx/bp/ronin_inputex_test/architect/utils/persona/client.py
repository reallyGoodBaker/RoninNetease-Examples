from ...core.export import ClientSubsystem, SubsystemClient
from ...component import BaseCompClient, Component, createComponent, getOneComponent
from ...core.basic import compClient, clientApi
from ...event import EventListener
from mod.common.minecraftEnum import EntityType

PlayerDefaultClientDef = {
    "materials": {
        "default": "entity_alphatest",
        "cape": "entity_alphatest",
        "animated": "player_animated",
        "spectator": "player_spectator"
    },
    "textures": {
        "default": "textures/entity/steve",
        "cape": "textures/entity/cape_invisible"
    },
    "geometry": {
        "default": "geometry.humanoid.custom",
        "cape": "geometry.cape"
    },
    "animations": {
        "root": "controller.animation.player.root",
        "base_controller": "controller.animation.player.base",
        "hudplayer": "controller.animation.player.hudplayer",
        "humanoid_base_pose": "animation.humanoid.base_pose",
        "look_at_target": "controller.animation.humanoid.look_at_target",
        "look_at_target_ui": "animation.player.look_at_target.ui",
        "look_at_target_default": "animation.humanoid.look_at_target.default",
        "look_at_target_gliding": "animation.humanoid.look_at_target.gliding",
        "look_at_target_swimming": "animation.humanoid.look_at_target.swimming",
        "look_at_target_inverted": "animation.player.look_at_target.inverted",
        "cape": "animation.player.cape",
        "move.arms": "animation.player.move.arms",
        "move.legs": "animation.player.move.legs",
        "swimming": "animation.player.swim",
        "swimming.legs": "animation.player.swim.legs",
        "riding.arms": "animation.player.riding.arms",
        "riding.legs": "animation.player.riding.legs",
        "holding": "animation.player.holding",
        "brandish_spear": "animation.humanoid.brandish_spear",
        "charging": "animation.humanoid.charging",
        "attack.positions": "animation.player.attack.positions",
        "attack.rotations": "animation.player.attack.rotations",
        "sneaking": "animation.player.sneaking",
        "bob": "animation.player.bob",
        "damage_nearby_mobs": "animation.humanoid.damage_nearby_mobs",
        "bow_and_arrow": "animation.humanoid.bow_and_arrow",
        "use_item_progress": "animation.humanoid.use_item_progress",
        "skeleton_attack": "animation.skeleton.attack",
        "sleeping": "animation.player.sleeping",
        "first_person_base_pose": "animation.player.first_person.base_pose",
        "first_person_empty_hand": "animation.player.first_person.empty_hand",
        "first_person_swap_item": "animation.player.first_person.swap_item",
        "first_person_attack_controller": "controller.animation.player.first_person_attack",
        "first_person_attack_rotation": "animation.player.first_person.attack_rotation",
        "first_person_attack_rotation_item": "animation.player.first_person.attack_rotation_item",
        "first_person_vr_attack_rotation": "animation.player.first_person.vr_attack_rotation",
        "first_person_walk": "animation.player.first_person.walk",
        "first_person_map_controller": "controller.animation.player.first_person_map",
        "first_person_map_hold": "animation.player.first_person.map_hold",
        "first_person_map_hold_attack": "animation.player.first_person.map_hold_attack",
        "first_person_map_hold_off_hand": "animation.player.first_person.map_hold_off_hand",
        "first_person_map_hold_main_hand": "animation.player.first_person.map_hold_main_hand",
        "first_person_crossbow_equipped": "animation.player.first_person.crossbow_equipped",
        "first_person_crossbow_hold": "animation.player.first_person.crossbow_hold",
        "first_person_breathing_bob": "animation.player.first_person.breathing_bob",
        "third_person_crossbow_equipped": "animation.player.crossbow_equipped",
        "third_person_bow_equipped": "animation.player.bow_equipped",
        "crossbow_hold": "animation.player.crossbow_hold",
        "crossbow_controller": "controller.animation.player.crossbow",
        "shield_block_main_hand": "animation.player.shield_block_main_hand",
        "shield_block_off_hand": "animation.player.shield_block_off_hand",
        "blink": "controller.animation.persona.blink",
        "fishing_rod": "animation.humanoid.fishing_rod",
        "holding_spyglass": "animation.humanoid.holding_spyglass",
        "first_person_shield_block": "animation.player.first_person.shield_block",
        "tooting_goat_horn": "animation.humanoid.tooting_goat_horn",
        "holding_brush": "animation.humanoid.holding_brush",
        "brushing": "animation.humanoid.brushing",
        "crawling": "animation.player.crawl",
        "crawling.legs": "animation.player.crawl.legs"
    },
    "render_controllers": [
        {
            "controller.render.player.first_person_spectator": "variable.is_first_person && query.is_spectator"
        },
        {
            "controller.render.player.third_person_spectator": "!variable.is_first_person && !variable.map_face_icon && query.is_spectator"
        },
        {
            "controller.render.player.first_person": "variable.is_first_person && !query.is_spectator"
        },
        {
            "controller.render.player.third_person": "!variable.is_first_person && !variable.map_face_icon && !query.is_spectator"
        },
        {
            "controller.render.player.map": "variable.map_face_icon"
        }
    ],
    "scripts": {
        "animate": [
            "root"
        ]
    },
}


@Component()
class PersonaRendererComponent(BaseCompClient):
    def onCreate(self, entityId):
        self.entityId = entityId
        self.actorRenderer = compClient.CreateActorRender(entityId)
        self.override = None
        self.playerPreloads = set()
        self.modified = False
        self.molang = compClient.CreateQueryVariable(entityId)
        self.shadowRoot = None
        if compClient.CreateEngineType(entityId).GetEngineTypeStr() == "minecraft:player":
            self._applyPlayerRenderConfToSelf()

    def broadcastRenderConf(self, jsonObj={}):
        PersonaEventsSubsystem.getInstance().sendServer('BroadcastPersonaChange', { 'id': self.entityId, 'data': jsonObj }) # type: ignore

    def broadcastResetConf(self):
        PersonaEventsSubsystem.getInstance().sendServer('BroadcastPersonaReset', { 'id': self.entityId }) # type: ignore

    def addActorRenderConf(self, jsonObject, actor=None): # type: ignore
        # type: (dict, str) -> None

        actorId = actor or self.entityId
        # 材质
        materials = jsonObject.get("materials")
        if materials:
            for name, material in materials.items():
                self.actorRenderer.AddRenderMaterialToOneActor(actorId, name, material)

        # 模型
        geometries = jsonObject.get("geometry")
        if geometries:
            for name, geometry in geometries.items():
                self.actorRenderer.AddGeometryToOneActor(actorId, name, geometry)

        # 贴图
        textures = jsonObject.get("textures")
        if textures:
            for name, texture in textures.items():
                self.actorRenderer.AddTextureToOneActor(actorId, name, texture)

        # 动画/动画控制器
        animations = jsonObject.get("animations")
        if animations:
            for name, animation in animations.items():
                if animation.startswith('controller.'):
                    self.actorRenderer.AddAnimationControllerToOneActor(actorId, name, animation)
                else:
                    self.actorRenderer.AddAnimationToOneActor(actorId, name, animation)

        # 粒子
        particles = jsonObject.get("particle_effects")
        if particles:
            for name, particle in particles.items():
                self.actorRenderer.AddParticleEffectToOneActor(actorId, name, particle)

        #音效
        sounds = jsonObject.get('sound_effects')
        if sounds:
            for name, sound in sounds.items():
                self.actorRenderer.AddSoundEffectToOneActor(actorId, name, sound)

        # 渲染控制器
        renderControllers = jsonObject.get("render_controllers")
        if renderControllers:
            for renderControllerDef in renderControllers:
                if isinstance(renderControllerDef, dict):
                    name, cond = renderControllerDef.items()[0] # type: ignore
                    self.actorRenderer.AddRenderControllerToOneActor(actorId, name, cond)
                else:
                    self.actorRenderer.AddRenderControllerToOneActor(actorId, renderControllerDef)

        # scripts
        scripts = jsonObject.get("scripts")
        if scripts:
            animates = scripts.get('animate')
            if animates:
                for animate in animates:
                    if isinstance(animate, dict):
                        name, cond = animate.items()[0] # type: ignore
                        self.actorRenderer.AddScriptAnimateToOneActor(actorId, name, cond, True)
                    else:
                        self.actorRenderer.AddScriptAnimateToOneActor(actorId, animate, True) # type: ignore

        self.actorRenderer.RebuildRenderForOneActor()

    @staticmethod
    def addActorTypeRenderConf(actorType, jsonObject):
        # type: (str, dict) -> None
        actorRenderer = compClient.CreateActorRender(clientApi.GetLevelId())

        # 材质
        materials = jsonObject.get("materials")
        if materials:
            for name, material in materials.items():
                actorRenderer.AddActorRenderMaterial(actorType, name, material)

        # 模型
        geometries = jsonObject.get("geometry")
        if geometries:
            for name, geometry in geometries.items():
                actorRenderer.AddActorGeometry(actorType, name, geometry)

        # 贴图
        textures = jsonObject.get("textures")
        if textures:
            for name, texture in textures.items():
                actorRenderer.AddActorTexture(actorType, name, texture)

        # 动画/动画控制器
        animations = jsonObject.get("animations")
        if animations:
            for name, animation in animations.items():
                if animation.startswith('controller.'):
                    actorRenderer.AddActorAnimationController(actorType, name, animation)
                else:
                    actorRenderer.AddActorAnimation(actorType, name, animation)

        # 粒子
        particles = jsonObject.get("particle_effects")
        if particles:
            for name, particle in particles.items():
                actorRenderer.AddActorParticleEffect(actorType, name, particle)

        #音效
        sounds = jsonObject.get('sound_effects')
        if sounds:
            for name, sound in sounds.items():
                actorRenderer.AddActorSoundEffect(actorType, name, sound)

        # 渲染控制器
        renderControllers = jsonObject.get("render_controllers")
        if renderControllers:
            for renderControllerDef in renderControllers:
                if isinstance(renderControllerDef, dict):
                    name, cond = renderControllerDef.items()[0] # type: ignore
                    actorRenderer.AddActorRenderController(actorType, name, cond)
                else:
                    actorRenderer.AddActorRenderController(actorType, renderControllerDef)

        # scripts
        scripts = jsonObject.get("scripts")
        if scripts:
            animates = scripts.get('animate')
            if animates:
                for animate in animates:
                    if isinstance(animate, dict):
                        name, cond = animate.items()[0] # type: ignore
                        actorRenderer.AddActorScriptAnimate(actorType, name, cond)
                    else:
                        actorRenderer.AddActorScriptAnimate(actorType, animate)
        actorRenderer.RebuildActorRender(actorType)

    def hasRenderController(self, name):
        return name in (self.actorRenderer.GetActorRenderParams(self.entityId, 'render_controllers') or [])

    def addPlayerRenderConf(self, jsonObject, rebuild=True):
        # 材质
        materials = jsonObject.get("materials")
        if materials:
            for name, material in materials.items():
                self.actorRenderer.AddPlayerRenderMaterial(name, material)

        # 模型
        geometries = jsonObject.get("geometry")
        if geometries:
            for name, geometry in geometries.items():
                self.actorRenderer.AddPlayerGeometry(name, geometry)

        # 贴图
        textures = jsonObject.get("textures")
        if textures:
            for name, texture in textures.items():
                self.actorRenderer.AddPlayerTexture(name, texture)

        # 动画/动画控制器
        animations = jsonObject.get("animations")
        if animations:
            for name, animation in animations.items():
                if animation.startswith('controller.'):
                    self.actorRenderer.AddPlayerAnimationController(name, animation)
                else:
                    self.actorRenderer.AddPlayerAnimation(name, animation)

        # 粒子
        particles = jsonObject.get("particle_effects")
        if particles:
            for name, particle in particles.items():
                self.actorRenderer.AddPlayerParticleEffect(name, particle)

        #音效
        sounds = jsonObject.get('sound_effects')
        if sounds:
            for name, sound in sounds.items():
                self.actorRenderer.AddPlayerSoundEffect(name, sound)

        # 渲染控制器
        renderControllers = jsonObject.get("render_controllers")
        if renderControllers:
            for renderControllerDef in renderControllers:
                if isinstance(renderControllerDef, dict):
                    name, cond = renderControllerDef.items()[0] # type: ignore
                    if self.hasRenderController(name):
                        self.actorRenderer.RemovePlayerRenderController(name)
                    self.actorRenderer.AddPlayerRenderController(name, cond)
                else:
                    if self.hasRenderController(renderControllerDef):
                        self.actorRenderer.RemovePlayerRenderController(renderControllerDef)
                    self.actorRenderer.AddPlayerRenderController(renderControllerDef)

        # scripts
        scripts = jsonObject.get("scripts")
        if scripts:
            animates = scripts.get('animate')
            if animates:
                for animate in animates:
                    if isinstance(animate, dict):
                        name, cond = animate.items()[0] # type: ignore
                        self.actorRenderer.AddPlayerScriptAnimate(name, cond, True)
                    else:
                        self.actorRenderer.AddPlayerScriptAnimate(animate, True) # type: ignore

        if rebuild:
            self.actorRenderer.RebuildPlayerRender()

    _PlayerPrefabs = []

    @staticmethod
    def addPlayerTypeRenderConf(jsonObject):
        PersonaRendererComponent._PlayerPrefabs.append(jsonObject)

    def _applyPlayerRenderConfToSelf(self):
        for playerPrefab in PersonaRendererComponent._PlayerPrefabs:
            self.addPlayerRenderConf(playerPrefab, False)
        self.actorRenderer.RebuildPlayerRender()

    def rebuildRender(self):
        if compClient.CreateEngineType(self.entityId).GetEngineType() == EntityType.Player:
            self.actorRenderer.RebuildPlayerRender()
        else:
            self.actorRenderer.RebuildRenderForOneActor()

    def changeActorRenderConf(self, jsonObject, actor=None, full=False, broadcast=True): # type: ignore
        # type: (dict, str, bool, bool) -> None
        """
        当full为False时，此方法不会修改 geometry, texture 和 particle_effects 的配置
        """

        actorId = actor or self.entityId
        actorOverride = {}

        # 材质
        materials = jsonObject.get("materials")
        if materials:
            actorOverride["materials"] = materials
            for name, material in materials.items():
                self.actorRenderer.AddRenderMaterialToOneActor(actorId, name, material)

        if full:
            # 模型
            geometries = jsonObject.get("geometry")
            if geometries:
                actorOverride["geometry"] = geometries
                print('[WARN] Geometries should be preloaded before use.')
                for name, geometry in geometries.items():
                    self.actorRenderer.AddGeometryToOneActor(actorId, name, geometry)

            # 贴图
            textures = jsonObject.get("textures")
            if textures:
                actorOverride["textures"] = textures
                print('[WARN] Textures should be preloaded before use.')
                for name, texture in textures.items():
                    self.actorRenderer.AddTextureToOneActor(actorId, name, texture)

            # 粒子
            particles = jsonObject.get("particle_effects")
            if particles:
                actorOverride["particle_effects"] = particles
                print('[WARN] Particle Effects should be preloaded before use.')
                for name, particle in particles.items():
                    self.actorRenderer.AddParticleEffectToOneActor(actorId, name, particle)

            #音效
            sounds = jsonObject.get('sound_effects')
            if sounds:
                print('[WARN] Sound Effects should be preloaded before use.')
                for name, sound in sounds.items():
                    self.actorRenderer.AddSoundEffectToOneActor(actorId, name, sound)

            # 渲染控制器
            renderControllers = jsonObject.get("render_controllers")
            if renderControllers:
                actorOverride["render_controllers"] = renderControllers
                for renderControllerDef in renderControllers:
                    if isinstance(renderControllerDef, dict):
                        name, cond = renderControllerDef.items()[0] # type: ignore
                        if self.hasRenderController(name):
                            self.actorRenderer.RemoveRenderControllerForOneActor(name) # type: ignore
                        self.actorRenderer.AddRenderControllerToOneActor(actorId, name, cond)
                    else:
                        if self.hasRenderController(renderControllerDef):
                            self.actorRenderer.RemoveRenderControllerForOneActor(renderControllerDef) # type: ignore
                        self.actorRenderer.AddRenderControllerToOneActor(actorId, renderControllerDef)


        # 动画/动画控制器
        animations = jsonObject.get("animations")
        if animations:
            actorOverride["animations"] = animations
            for name, animation in animations.items():
                if animation.startswith('controller.'):
                    self.actorRenderer.AddAnimationControllerToOneActor(actorId, name, animation)
                else:
                    self.actorRenderer.AddAnimationToOneActor(actorId, name, animation)

        # scripts
        scripts = jsonObject.get("scripts")
        if scripts:
            actorOverride["scripts"] = scripts
            animates = scripts.get('animate')
            if animates:
                for animate in animates:
                    if isinstance(animate, dict):
                        name, cond = animate.items()[0] # type: ignore
                        self.actorRenderer.AddScriptAnimateToOneActor(actorId, name, cond)
                    else:
                        self.actorRenderer.AddScriptAnimateToOneActor(actorId, animate)

        self.actorRenderer.RebuildRenderForOneActor()
        self.modified = True
        if broadcast:
            self.broadcastRenderConf(actorOverride)

    def changePlayerRenderConf(self, jsonObject={}, full=False, broadcast=True):
        # type: (dict, bool, bool) -> None
        """
        当full为False时，此方法不会修改 geometry, texture 和 particle_effects 的配置
        """

        overrideObj = {
            'geometry': [],
            'renderController': [],
            'animController': [],
        }
        overrideSnapshot = {}

        # 材质
        materials = jsonObject.get("materials")
        if materials:
            overrideSnapshot["materials"] = materials
            for name, material in materials.items():
                self.actorRenderer.AddPlayerRenderMaterial(name, material)

        if full:
            # 模型
            geometries = jsonObject.get("geometry")
            if geometries:
                overrideSnapshot["geometry"] = geometries
                print('[WARN] Geometries should be preloaded before use.')
                for name, geometry in geometries.items():
                    overrideObj['geometry'].append(name)
                    self.actorRenderer.AddPlayerGeometry(name, geometry)

            # 贴图
            textures = jsonObject.get("textures")
            if textures:
                overrideSnapshot["textures"] = textures
                print('[WARN] Textures should be preloaded before use.')
                for name, texture in textures.items():
                    self.actorRenderer.AddPlayerTexture(name, texture)

            # 粒子
            particles = jsonObject.get("particle_effects")
            if particles:
                overrideSnapshot["particle_effects"] = particles
                print('[WARN] Particle Effects should be preloaded before use.')
                for name, particle in particles.items():
                    self.actorRenderer.AddPlayerParticleEffect(name, particle)

            #音效
            sounds = jsonObject.get('sound_effects')
            if sounds:
                print('[WARN] Sound Effects should be preloaded before use.')
                for name, sound in sounds.items():
                    self.actorRenderer.AddPlayerSoundEffect(name, sound)

            # 渲染控制器
            renderControllers = jsonObject.get("render_controllers")
            if renderControllers:
                overrideSnapshot["render_controllers"] = renderControllers
                for renderControllerDef in renderControllers:
                    if isinstance(renderControllerDef, dict):
                        name, cond = renderControllerDef.items()[0] # type: ignore
                        overrideObj['renderController'].append(name)
                        if self.hasRenderController(name):
                            self.actorRenderer.RemovePlayerRenderController(name)
                        self.actorRenderer.AddPlayerRenderController(name, cond)
                    else:
                        overrideObj['renderController'].append(renderControllerDef)
                        if self.hasRenderController(renderControllerDef):
                            self.actorRenderer.RemovePlayerRenderController(renderControllerDef)
                        self.actorRenderer.AddPlayerRenderController(renderControllerDef)

        # 动画/动画控制器
        animations = jsonObject.get("animations")
        if animations:
            overrideSnapshot["animations"] = animations
            for name, animation in animations.items():
                if animation.startswith('controller.'):
                    overrideObj['animController'].append(name)
                    self.actorRenderer.AddPlayerAnimationController(name, animation)
                else:
                    self.actorRenderer.AddPlayerAnimation(name, animation)

        # scripts
        scripts = jsonObject.get("scripts")
        if scripts:
            overrideSnapshot["scripts"] = scripts
            animates = scripts.get('animate')
            if animates:
                for animate in animates:
                    if isinstance(animate, dict):
                        name, cond = animate.items()[0] # type: ignore
                        self.actorRenderer.AddPlayerScriptAnimate(name, cond)
                    else:
                        self.actorRenderer.AddPlayerScriptAnimate(animate)

        self.actorRenderer.RebuildPlayerRender()
        self.modified = True
        self.override = overrideObj
        if broadcast:
            self.broadcastRenderConf(overrideSnapshot)

    def showHand(self, visible=True, mode=0):
        self.actorRenderer.SetPlayerItemInHandVisible(visible, mode)

    def changeRenderConf(self, jsonObject, broadcast=True, full=False):
        if compClient.CreateEngineType(self.entityId).GetEngineType() == EntityType.Player:
            self.changePlayerRenderConf(jsonObject, full, broadcast)
        else:
            self.changeActorRenderConf(jsonObject, full, broadcast) # type: ignore

    def addRenderConf(self, jsonObject, rebuild=True):
        if compClient.CreateEngineType(self.entityId).GetEngineType() == EntityType.Player:
            self.addPlayerRenderConf(jsonObject, rebuild)
        else:
            self.addActorRenderConf(jsonObject, rebuild) # type: ignore

    def resetActorRenderConf(self, broadcast=True):
        if not self.modified:
            return

        self.actorRenderer.ResetRenderForOneActor()
        self.modified = False
        if broadcast:
            self.broadcastResetConf()

    def resetPlayerRenderConf(self, broadcast=True, rebuild=True):
        if not self.modified:
            return

        renderer = self.actorRenderer
        if self.override:
            animControllers = self.override['animController']
            renderControllers = self.override['renderController']
            geometry = self.override['geometry']

            for geo in geometry:
                renderer.RemovePlayerGeometry(geo)

            for anim in animControllers:
                renderer.RemovePlayerAnimationController(anim)

            for renderController in renderControllers:
                renderer.RemovePlayerRenderController(renderController)

        renderer.AddPlayerAnimationController('root', 'controller.animation.player.root')
        if rebuild:
            renderer.RebuildPlayerRender()
        self.modified = False
        self.override = None
        if broadcast:
            self.broadcastResetConf()

    def resetRenderConf(self, broadcast=True, rebuild=True):
        if compClient.CreateEngineType(self.entityId).GetEngineType() == EntityType.Player:
            self.resetPlayerRenderConf(broadcast, rebuild)
        else:
            self.resetActorRenderConf(broadcast)

    def shadowPlayerRootAnim(self, anim=None): # type: ignore
        # type: (str) -> None
        """
        使用一个动画遮蔽玩家根动画，可以为空
        """
        self.actorRenderer.AddPlayerScriptAnimate('root', '0')
        if anim:
            self.actorRenderer.AddPlayerScriptAnimate(anim, '1')
            self.shadowRoot = anim
        self.actorRenderer.RebuildPlayerRender()

    def restorePlayerRootAnim(self):
        shadowRoot = self.shadowRoot
        self.actorRenderer.AddPlayerAnimationController('root', 'controller.animation.player.root')
        self.actorRenderer.AddPlayerScriptAnimate('root', '1', True)
        if shadowRoot:
            self.actorRenderer.AddPlayerScriptAnimate(shadowRoot, '0')
            self.shadowRoot = None
        self.actorRenderer.RebuildPlayerRender()

def createPersona(id):
    return createComponent(id, PersonaRendererComponent)

def getPersona(id):
    return getOneComponent(id, PersonaRendererComponent)

RenderConfKeys = (
    'geometry',
    'textures',
    'materials'
    'particle_effects',
    'animations',
    'render_controllers',
    'scripts',
)

PlayerActorTypes = (
    'minecraft:player',
    'player',
)


@SubsystemClient
class PersonaEventsSubsystem(ClientSubsystem):

    @EventListener('PersonaChangeServer', isCustomEvent=True)
    def onPersonaChangeServer(self, event):
        if not event.id:
            return
        personaRenderer = getPersona(event.id) # type: ignore
        if personaRenderer:
            personaRenderer.changeRenderConf(event.data, False, full=True)

    @EventListener('PersonaResetServer', isCustomEvent=True)
    def onPersonaResetServer(self, event):
        personaRenderer = getPersona(event.id) # type: ignore
        if personaRenderer:
            personaRenderer.resetRenderConf(False)

    @EventListener('PersonaChangeClientAuthed', isCustomEvent=True)
    def onPersonaChangeServerAuth(self, event):
        if not event.id:
            return
        personaRenderer = getPersona(event.id) # type: ignore
        if personaRenderer:
            personaRenderer.changeRenderConf(event.data, False, True)

    @EventListener('PersonaResetClientAuthed', isCustomEvent=True)
    def onPersonaResetServerAuth(self, event):
        personaRenderer = getPersona(event.id) # type: ignore
        if personaRenderer:
            personaRenderer.resetRenderConf(False)

    @EventListener('OnLocalPlayerStopLoading')
    def onLocalPlayerStopLoading(self, _):
        createPersona(clientApi.GetLocalPlayerId())
        self.sendServer('PersonaChangeClientInit', {})

    @EventListener('AddPlayerCreatedClientEvent')
    def onAddPlayerCreatedClientEvent(self, event):
        if event.playerId != clientApi.GetLocalPlayerId():
            createPersona(event.playerId)