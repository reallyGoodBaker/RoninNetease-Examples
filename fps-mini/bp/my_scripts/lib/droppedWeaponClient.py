# -*- coding: utf-8 -*-
"""丢出的枪: 客户端只做一件小事 —— 让地上的枪不投影。

掉落物实体用的是武器自己的渲染控制器, 模型/贴图都由 entity json 决定,
不需要在这里同步任何东西(地上躺的东西不值得每个实体多写一堆 molang 变量)。

用 AddEntityClientEvent 本地筛出 template:dropped_* 即可, 不依赖服务端广播。
"""
from ..engine.architect.compact import (
    SubsystemClient, ClientSubsystem,
    EventListener, events, compClient, addTimer,
)

TYPE_PREFIX = 'template:dropped_'
# 实体刚创建时模型组件可能还没就绪, 隔一会儿补一次(幂等)
REAPPLY_DELAYS = (0.25, 1.0)


def _sid(entityId):
    # type: (object) -> str
    return str(entityId) if entityId is not None else None


@SubsystemClient
class DroppedWeaponClientSystem(ClientSubsystem):
    """掉落武器实体生成时, 关掉它的影子。"""

    @EventListener()
    def onEntityAdded(self, ev=events.AddEntityClientEvent()):
        engineType = getattr(ev, 'engineTypeStr', None) or ''
        if not engineType.startswith(TYPE_PREFIX):
            return
        entityId = _sid(getattr(ev, 'id', None))
        if not entityId:
            return
        self._hideShadow(entityId)
        for delay in REAPPLY_DELAYS:
            addTimer(delay, lambda e=entityId: self._hideShadow(e), False)

    @staticmethod
    def _hideShadow(entityId):
        # type: (str) -> None
        """SetEntityShadowShow 是客户端 ModelComponent 的接口。"""
        try:
            compClient.CreateModel(entityId).SetEntityShadowShow(False)
        except Exception:
            pass
