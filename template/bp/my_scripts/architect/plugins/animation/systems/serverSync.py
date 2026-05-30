import time

from ....compact import remote, Remote, ServerSubsystem, SubsystemServer



FnNameSyncDilation = 'AnimationExSubsystem.syncDilation'
FnNamePlayFromServer = 'AnimationExSubsystem.playFromServer'
FnNameStopFromServer = 'AnimationExSubsystem.stopFromServer'


@SubsystemServer
class AnimExServer(ServerSubsystem):

    @Remote
    def updateDilation(self, instigator, dilation):
        remote.server.callEvery(
            FnNameSyncDilation,
            instigator, dilation
        )

    @Remote
    def _syncPlay(self, actorId, animKey, layer='default', replay=False, playRate=1, startTime=time.time()):
        remote.server.callEvery(
            FnNamePlayFromServer,
            actorId, animKey, layer, replay, playRate, startTime, True
        )

    @Remote
    def _syncStop(self, actorId, key, layer, noBlending):
        remote.server.callEvery(
            FnNameStopFromServer,
            actorId, key, layer, noBlending
        )

    @staticmethod
    def play(actorId, animKey, layer='default', replay=False, playRate=1):
        startTime = time.time()
        remote.server.call(
            actorId, FnNamePlayFromServer,
            actorId, animKey, layer, replay, playRate, startTime, False
        )
        remote.server.callEvery(
            FnNamePlayFromServer,
            actorId, animKey, layer, replay, playRate, startTime, True
        )

    @staticmethod
    def stop(actorId, key, layer, noBlending):
        remote.server.callEvery(
            FnNameStopFromServer,
            actorId, key, layer, noBlending
        )