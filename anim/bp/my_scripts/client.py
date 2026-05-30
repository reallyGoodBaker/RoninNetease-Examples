from .architect.compact import *
from .architect.plugins.animation.components.animClient import AnimationExComponent, AnimationEasingTypes, AnimationEasingConf
from .architect.utils.persona.client import PersonaRendererComponent
from .architect.plugins.input.client import InputAction, InputState, InputExComponent

from .assets.animations import GenericMapping

PlayerPersona = {
    'geometry': {
        'default': 'geometry.standard_steve'
    },
    'animations': {
        'root': 'animation.standard_steve.idle'
    },
    'scripts': {
        'animate': [
            { 'root' }
        ]
    }
}

ItemHoldingAnimMapping = {
    'minecraft:diamond_sword': 'diamond',
    'minecraft:wooden_sword': 'wood',
    'minecraft:iron_sword': 'iron',
}

@SubsystemClient
class AnimPlayerClient(ClientSubsystem):
    def onInit(self):
        self.moveInputing = False

    @EventListener()
    def onPlayerSwap(self, ev=events.OnCarriedNewItemChangedClientEvent()):
        name = ev.itemDict['newItemName']
        animKey = ItemHoldingAnimMapping.get(name, 'idle')
        animEx = getOneComponent(localPlayerId(), AnimationExComponent)
        inputEx = getOneComponent(localPlayerId(), InputExComponent)
        if animEx and inputEx:
            animEx.play(animKey, 'holding')
            inputEx.preventAttack = True
            if animKey == 'diamond':
                inputEx.enableMapping('IM_Attack')
            elif animKey == 'idle':
                inputEx.preventAttack = False
                inputEx.disableMapping('IM_Attack')

    @EventListener()
    def onPlayerCreated(self, ev=events.AddPlayerCreatedClientEvent()):
        id = ev.playerId
        animEx = getOrCreateComponent(id, AnimationExComponent)
        renderer = getOrCreateComponent(id, PersonaRendererComponent)
        inputEx = getOrCreateComponent(id, InputExComponent)
        inputEx.preventAttack = True
        renderer.addRenderConf(PlayerPersona, False)
        animEx.registerAnimations(GenericMapping)
        animEx.updateActorAnimDef()
        for animKey in GenericMapping.keys():
            animEx.registerEasing(
                animKey,
                AnimationEasingConf(1, 0.15, AnimationEasingTypes.SINE),
                AnimationEasingConf(0, 0.24, AnimationEasingTypes.CUBIC),
            )

    @Sched.Render()
    def onPlayerMove(self):
        actorMotion = compClient.CreateActorMotion(localPlayerId())
        x, z = actorMotion.GetInputVector()
        isMoving = x != 0 or z != 0
        if isMoving != self.moveInputing:
            self.broadcast('walk', { 'moving': isMoving })
            self.moveInputing = isMoving

    @CustomEvent('walk')
    def onPlayerWalk(self, ev):
        moving = ev.moving
        animEx = getOneComponent(localPlayerId(), AnimationExComponent)
        if moving:
            animEx.play('walk', 'loco')
        else:
            animEx.stop('walk', 'loco')

    @InputAction('IA_Attack')
    def onPlayerDiamondAttack(self, value):
        animEx = getOneComponent(localPlayerId(), AnimationExComponent)
        item = compClient.CreateItem(localPlayerId())
        carried = item.GetCarriedItem()
        if not carried or carried['newItemName'] != 'minecraft:diamond_sword':
            return
        if animEx:
            animEx.play('attack', 'holding')