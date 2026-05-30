from .engine.architect.compact import *
from .engine.architect.plugins.input.client import InputAction, InputState, InputExComponent

JUMP_POWER = 0.5
MOVE_SPEED = 0.5
FLY_SPEED = 1
VERTICAL_FLY_SPEED = 0.1


@SubsystemClient
class TestClient(ClientSubsystem):

    @EventListener('OnLocalPlayerStopLoading')
    def onLocalPlayerStopLoading(self, ev):
        inputEx = getOneSingletonComponent(InputExComponent)
        # 启用 'move', 'spying' 映射
        inputEx.enableMappings(
            'move', 'spying',
        )
        # 屏蔽原版走路逻辑
        operation = LevelClient.getInstance().operation
        operation.SetCanMove(False)
        operation.SetCanJump(False)

    @InputAction('laravelMovement')
    def iaMove(self, ev):
        # 通过输入控制玩家移动
        x, y = ev.value
        motion = compClient.CreateActorMotion(localPlayerId())
        cam = LevelClient.getInstance().camera
        forward = vec(cam.GetForward())
        up = vec((0, 1, 0))
        right = normalize(cross(forward, up))
        laravelForward = normalize(cross(up, right))
        moveVec = (y * laravelForward + x * right) * MOVE_SPEED
        mx, mz = moveVec.x, moveVec.z
        my = motion.GetMotion()[1]
        motion.SetMotion((mx, my, mz))

    @InputAction('flyMove')
    def iaFlyMove(self, ev):
        # 通过输入控制玩家移动
        x, y = ev.value
        motion = compClient.CreateActorMotion(localPlayerId())
        cam = LevelClient.getInstance().camera
        forward = vec(cam.GetForward())
        up = vec((0, 1, 0))
        right = normalize(cross(forward, up))
        moveVec = (y * forward + x * right) * FLY_SPEED
        motion.SetMotion(tup(moveVec))

    @InputAction('jump')
    def iaJump(self, _):
        # 通过输入控制玩家跳跃
        attr = compClient.CreateAttr(localPlayerId())
        # 如果玩家在地面上，则执行跳跃
        if attr.isEntityOnGround():
            motion = compClient.CreateActorMotion(localPlayerId())
            x, _, z = motion.GetMotion()
            motion.SetMotion((x, JUMP_POWER, z))

    @InputAction('startFly')
    def iaStartFly(self, _):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.disableMapping('move')
        inputEx.enableMapping('fly')
        print ('start fly')

    @InputAction('stopFly')
    def iaStopFly(self, _):
        inputEx = getOneSingletonComponent(InputExComponent)
        inputEx.disableMapping('fly')
        inputEx.enableMapping('move')
        print ('stop fly')

    @InputAction('spying')
    def iaSpying(self, _):
        LevelClient.getInstance().playerView.SetPlayerFovScale(0.1)

    @InputAction('spying', InputState.Completed)
    def iaCompleteSpying(self, _):
        LevelClient.getInstance().playerView.SetPlayerFovScale(1)