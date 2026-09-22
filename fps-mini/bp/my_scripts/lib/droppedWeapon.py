# -*- coding: utf-8 -*-
"""丢出的枪械：用带模型的实体代替原版掉落物, 靠近自动捡回。

原版掉落的物品是 item entity, 只会显示 2D 图标。这里在掉落的那一瞬间:
  1. 用 CreateItem(levelId).GetDroppedItem 读出掉落物
  2. 是枪 -> 生成 template:dropped_<weapon> (带武器模型), 成功后再销毁原版掉落物
  3. 每 SCAN_INTERVAL 秒检查一次: 附近有玩家就 SpawnItemToPlayerInv 还给他,
     没人捡就等 LIFETIME 秒后消失

掉落物只显示武器本身 (默认外观), 不做配件/染色的同步 —— 那需要在每个实体上
多写一堆 molang 变量, 地上躺的东西不值得这个开销。

实体/模型资源由 scripts/gen-dropped-weapon.mjs 生成。
"""
import time

from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    EventListener, Sched,
    Location, compServer, serverApi,
)
from ..engine.architect.core.log import info
from .gunSync import getGunItemNames, isGunItemName, itemNameOf

# 实体 identifier 前缀 / 族: 必须和 scripts/gen-dropped-weapon.mjs 里的一致
TYPE_PREFIX = 'template:dropped_'
FAMILY = 'dropped_weapon'

DEBUG = True             # 排查问题用, 稳定后可以关掉
CLEAN_ORPHANS = False    # 是否清理重启后遗留的"空壳"掉落物实体

PICKUP_RADIUS = 1.8      # 捡起距离(格)
PICKUP_DELAY = 1.0       # 丢出后多久才能被捡(秒), 免得刚脱手就被自己捡回来
LIFETIME = 300.0         # 存在时间(秒), 和原版掉落物差不多
SCAN_INTERVAL = 0.5      # 扫描间隔(秒)
ORPHAN_RADIUS = 16.0     # 清理残留时的扫描半径(格)


def _sid(entityId):
    # type: (object) -> str
    """统一实体 id 类型。

    不同接口返回的 id 类型不一定一样(有的 str 有的 int), 直接用原值当字典 key
    会出现"明明是同一条实体却对不上"的问题。
    """
    return str(entityId) if entityId is not None else None


@SubsystemServer
class DroppedWeaponSystem(ServerSubsystem):
    """把丢在地上的枪做成实体, 并且能捡回来。"""

    def onInit(self):
        self.levelId = serverApi.GetLevelId()   # GetDroppedItem 要用 levelId 建 ItemComponent
        # entityId(str) -> {'item': itemDict, 'weapon': str, 'born': float, 'owner': str}
        self.dropped = {}
        self.lastScan = 0.0

    def _log(self, msg, *args):
        if DEBUG:
            info('[droppedWeapon] ' + msg, *args)

    # ------------------------------------------------------------ 位置 / 玩家

    def _playersNear(self, pos, radius):
        # type: (tuple, float) -> list
        """附近玩家。

        直接用玩家列表 + 距离判断, 不走 GetEntitiesAround:
        后者的 filter 参数格式各版本不一致, 一旦不生效就会静默返回空列表,
        表现就是"枪丢在地上但谁也捡不起来"。
        """
        result = []
        try:
            playerIds = serverApi.GetPlayerList() or []
        except Exception:
            return result
        r2 = radius * radius
        for playerId in playerIds:
            try:
                ppos = compServer.CreatePos(playerId).GetPos()
            except Exception:
                continue
            dx = ppos[0] - pos[0]
            dy = ppos[1] - pos[1]
            dz = ppos[2] - pos[2]
            if dx * dx + dy * dy + dz * dz <= r2:
                result.append(playerId)
        return result

    def _giveBack(self, playerId, itemDict):
        # type: (str, dict) -> bool
        """把枪塞回玩家背包。明确失败时返回 False, 掉落物继续留在地上。"""
        try:
            ret = compServer.CreateItem(playerId).SpawnItemToPlayerInv(itemDict, playerId, -1)
        except Exception as exc:
            self._log('SpawnItemToPlayerInv 异常: %s', exc)
            return False
        self._log('SpawnItemToPlayerInv(player=%s) -> %r', playerId, ret)
        # 只有明确返回 False 才当失败, 免得返回值不是布尔时把掉落物吃掉
        return ret is not False

    # ------------------------------------------------------------ 掉落

    @EventListener('PlayerDropItemServerEvent')
    def onPlayerDropItem(self, ev):
        playerId = getattr(ev, 'playerId', None)
        itemEntityId = getattr(ev, 'itemEntityId', None)
        self._log('掉落事件 player=%s itemEntity=%s', playerId, itemEntityId)
        if not playerId or not itemEntityId:
            return
        try:
            itemDict = compServer.CreateItem(self.levelId).GetDroppedItem(itemEntityId)
        except Exception as exc:
            self._log('GetDroppedItem 失败: %s', exc)
            return
        itemName = itemNameOf(itemDict)
        self._log('掉落物 itemName=%s', itemName)
        if not isGunItemName(itemName):
            return
        weapon = getGunItemNames().get(itemName)
        if not weapon:
            return

        pos = compServer.CreatePos(itemEntityId).GetPos()
        dim = compServer.CreateDimension(itemEntityId).GetEntityDimensionId()
        rot = (0, 0)
        try:
            rot = compServer.CreateRot(itemEntityId).GetRot()
        except Exception:
            pass

        # 先生成替换实体, 成功了再销毁原版掉落物, 免得实体生成失败把物品弄丢
        entityId = self.spawnEntity(TYPE_PREFIX + weapon, Location(pos, dim), rot)
        self._log('生成 %s -> entityId=%r pos=%s dim=%s', TYPE_PREFIX + weapon, entityId, pos, dim)
        if not entityId:
            return
        self.destroyEntity(itemEntityId)
        self.dropped[_sid(entityId)] = {
            'item': itemDict,
            'weapon': weapon,
            'born': time.time(),
            'owner': _sid(playerId),
        }

    # ------------------------------------------------------------ 拾取 / 消失

    def _cleanOrphans(self):
        """清掉表里没有的掉落武器实体。

        脚本表只活在内存里, 重启/热重载后会丢; 那些实体已经没有 itemDict,
        捡不起来也不会消失, 扫到就清掉。默认关闭(CLEAN_ORPHANS)。
        """
        try:
            players = serverApi.GetPlayerList() or []
        except Exception:
            return
        filters = {
            'all_of': [
                {'subject': 'other', 'test': 'is_family', 'value': FAMILY}
            ]
        }
        for playerId in players:
            try:
                found = compServer.CreateGame(playerId).GetEntitiesAround(playerId, ORPHAN_RADIUS, filters) or []
            except Exception:
                continue
            for entityId in found:
                if _sid(entityId) not in self.dropped:
                    self._log('清理残留掉落物实体 %s', entityId)
                    self.destroyEntity(entityId)

    @Sched.Tick()
    def updateDroppedWeapons(self):
        now = time.time()
        if now - self.lastScan < SCAN_INTERVAL:
            return
        self.lastScan = now
        if CLEAN_ORPHANS:
            self._cleanOrphans()
        for key in list(self.dropped.keys()):
            if self._updateOne(key, self.dropped[key], now):
                self.dropped.pop(key, None)

    def _updateOne(self, entityId, info, now):
        # type: (str, dict, float) -> bool
        """返回 True 表示这条掉落物已经处理完(可以从表里删掉)。"""
        age = now - info['born']
        if age >= LIFETIME:
            self._log('掉落物 %s 超时消失', entityId)
            self.destroyEntity(entityId)
            return True
        if age < PICKUP_DELAY:
            return False
        try:
            pos = compServer.CreatePos(entityId).GetPos()
        except Exception as exc:
            self._log('CreatePos(%s) 失败: %s', entityId, exc)
            return False
        players = self._playersNear(pos, PICKUP_RADIUS)
        if not players:
            return False
        self._log('掉落物 %s 附近玩家=%s', entityId, players)
        for playerId in players:
            if self._giveBack(playerId, info['item']):
                self._log('掉落物 %s 被 %s 捡走', entityId, playerId)
                self.destroyEntity(entityId)
                return True
        return False
