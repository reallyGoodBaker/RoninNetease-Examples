from ....engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    SubsystemManager,
)

@SubsystemServer
class ShooterIndicatorReceiver(ServerSubsystem):

    def onReady(self):
        SubsystemManager.getInstance().bus.register(
            'ShooterIndicatorServer.hit',
            self.onRecev
        )

    # 由于是服务器发送的总线事件，所以需要从服务端重新发送到客户端
    def onRecev(self, playerId, isHeadShot, willKill, target, damage):
        self.sendClient(
            playerId,
            'showHitEffect',
            {
                'isHeadShot': isHeadShot,
                'kill': willKill,
                'target': target,
                'damage': damage
            }
        )