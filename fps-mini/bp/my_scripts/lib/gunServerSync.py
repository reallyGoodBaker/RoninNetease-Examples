# -*- coding: utf-8 -*-
"""Server-authoritative gun storage sync.

The weapon item's extraId is used only as an opaque per-gun uid. The actual gun
state (ammo/attachments/appearance) lives in server KV. The client requests the
state every time a gun is carried; the server creates the storage record when the
uid does not exist yet.

This keeps the client simple and avoids versioning state blobs inside itemDict.
"""
import copy
import random
import time

from ..engine.architect.compact import (
    ServerSubsystem, SubsystemServer,
    Remote, EventListener, events,
    compServer, serverApi, addTimer,
)
from .gunSync import (
    defaultGunStorage,
    isGunItemName,
    itemNameOf,
)
from .serverAuth import getOrCreateGunStorage

ItemPosType = serverApi.GetMinecraftEnum().ItemPosType

_GUN_ID_PREFIX = 'fpsm:'


def _makeGunUid():
    # type: () -> str
    millis = int(time.time() * 1000)
    entropy = random.getrandbits(48)
    return '{}{:x}{:012x}'.format(_GUN_ID_PREFIX, millis, entropy)[-64:]


@SubsystemServer
class GunServerSyncSystem(ServerSubsystem):
    """Create/read server storage records for gun items."""

    def onInit(self):
        # type: () -> None
        pass
        pass

    # ---------------------------------------------------------------
    # Item helpers
    # ---------------------------------------------------------------

    def _itemComp(self, playerId):
        # type: (str) -> object
        return compServer.CreateItem(playerId)

    def _readCarried(self, playerId):
        # type: (str) -> dict | None
        itemComp = self._itemComp(playerId)
        try:
            return itemComp.GetEntityItem(
                ItemPosType.CARRIED, 0, True
            )
        except Exception as errorObject:
            pass
            return None

    def _writeCarried(self, playerId, itemDict):
        # type: (str, dict) -> bool
        itemComp = self._itemComp(playerId)
        try:
            return bool(itemComp.SetEntityItem(
                ItemPosType.CARRIED, itemDict, 0
            ))
        except Exception as errorObject:
            pass
            return False

    def _ensureItemState(self, playerId, posType, itemDict, slot):
        # type: (str, object, dict | None, int) -> tuple | None
        """Give a gun item a uid and make sure its server record exists."""
        if not itemDict:
            return None
        itemName = itemNameOf(itemDict)
        if not isGunItemName(itemName):
            return None

        uid = itemDict.get('extraId') or ''
        if not uid:
            uid = _makeGunUid()
            updated = copy.deepcopy(itemDict)
            updated['extraId'] = uid
            itemComp = self._itemComp(playerId)
            try:
                ok = bool(itemComp.SetEntityItem(posType, updated, slot))
            except Exception as errorObject:
                pass
                ok = False
            if not ok:
                pass
                return None
            pass

        state = self._loadState(uid, itemName)
        return uid, state

    def _scanPlayerGuns(self, playerId):
        # type: (str) -> None
        """Scan all inventory/carried gun items after login.

        This gives existing items a server uid even if the client never asks
        while they are not carried, and upgrades old records to the current
        schema (e.g. adds appearance).
        """
        pass
        try:
            itemComp = self._itemComp(playerId)
            carried = itemComp.GetEntityItem(ItemPosType.CARRIED, 0, True)
            if carried:
                self._ensureItemState(
                    playerId, ItemPosType.CARRIED, carried, 0
                )
            inventory = itemComp.GetPlayerAllItems(
                ItemPosType.INVENTORY, True
            ) or []
            for slot, itemDict in enumerate(inventory):
                if itemDict:
                    self._ensureItemState(
                        playerId, ItemPosType.INVENTORY, itemDict, slot
                    )
        except Exception as errorObject:
            pass
        pass

    # ---------------------------------------------------------------
    # Storage helpers
    # ---------------------------------------------------------------

    def _loadState(self, uid, itemName):
        # type: (str, str) -> dict
        """Return a normalized server state, creating/upgrading it if needed."""
        view = getOrCreateGunStorage(uid, itemName)
        record = view.cache.get(uid)
        if not isinstance(record, dict):
            record = defaultGunStorage(itemName)
            view.set(uid, copy.deepcopy(record))
            return copy.deepcopy(record)

        record = copy.deepcopy(record)
        changed = False
        # Old records created before server-authoritative ammo existed used
        # ammoCount=0 as a default, which was never a real saved count.
        # Upgrade them to -1 (uninitialized -> full mag) once.
        if record.get('version') != 1:
            record['version'] = 1
            record['ammoCount'] = -1
            changed = True
        if record.get('itemName') != itemName:
            record['itemName'] = itemName
            changed = True
        if not isinstance(record.get('attachments'), dict):
            record['attachments'] = {}
            changed = True
        if not isinstance(record.get('appearance'), dict):
            record['appearance'] = {}
            changed = True
        if 'ammoCount' not in record:
            record['ammoCount'] = -1
            changed = True

        if changed:
            view.set(uid, copy.deepcopy(record))
        return record

    def _currentStateForCarried(self, playerId, requestedName):
        # type: (str, str) -> tuple
        """Return (uid, state) or error payload for the carried gun."""
        carried = self._readCarried(playerId)
        actualName = itemNameOf(carried)
        if not isGunItemName(actualName) or actualName != requestedName:
            return None, {
                'ok': False,
                'code': 'CARRIED_CHANGED',
                'uid': '',
                'state': None,
            }

        uid = carried.get('extraId') or ''
        if not uid:
            uid = _makeGunUid()
            updated = copy.deepcopy(carried)
            updated['extraId'] = uid
            if not self._writeCarried(playerId, updated):
                return None, {
                    'ok': False,
                    'code': 'WRITE_FAILED',
                    'uid': '',
                    'state': None,
                }
            pass

        state = self._loadState(uid, actualName)
        return uid, state

    def _resolveRequestedState(self, playerId, itemName, extraId):
        # type: (str, str, str) -> tuple
        """Resolve state using the uid the client already has.

        When extraId is present we do not require the server carried slot to
        match yet: client carried-change events can arrive before the server
        slot has caught up, and the uid alone is enough to load the record.
        When extraId is empty we still need the carried item so the server can
        create and write a fresh uid.
        """
        if extraId:
            uid = str(extraId)
            return uid, self._loadState(uid, itemName)
        return self._currentStateForCarried(playerId, itemName)

    # ---------------------------------------------------------------
    # Server-side item appearance events
    # ---------------------------------------------------------------

    @EventListener()
    def onPlayerAdded(self, ev=events.AddServerPlayerEvent()):
        # type: (object) -> None
        """Scan after login so pre-existing weapons get server state."""
        playerId = ev.id

        def scan():
            self._scanPlayerGuns(playerId)

        addTimer(1.0, scan, False)

    @EventListener()
    def onCarriedChanged(self, ev=events.OnCarriedNewItemChangedServerEvent()):
        # type: (object) -> None
        self._ensureItemState(
            ev.playerId, ItemPosType.CARRIED, ev.newItemDict, 0
        )

    @EventListener()
    def onInventoryChanged(self, ev=events.InventoryItemChangedServerEvent()):
        # type: (object) -> None
        self._ensureItemState(
            ev.playerId, ItemPosType.INVENTORY, ev.newItemDict, ev.slot
        )

    # ---------------------------------------------------------------
    # Client RPCs
    # ---------------------------------------------------------------

    @Remote
    def ensureGunState(self, playerId, itemName, extraId):
        # type: (str, str, str) -> dict
        """Fetch server state for the currently carried gun.
        """
        if not isinstance(itemName, str) or not isGunItemName(itemName):
            pass
            return {
                'ok': False,
                'code': 'UNKNOWN_ITEM',
                'uid': '',
                'state': None,
            }

        uid, state = self._resolveRequestedState(playerId, itemName, extraId)
        if uid is None:
            pass
            return state

        result = {
            'ok': True,
            'code': 'OK',
            'uid': uid,
            'state': state,
        }
        return result

    @Remote
    def setAppearance(self, playerId, itemName, extraId, appearance):
        # type: (str, str, str, dict) -> dict
        """Persist only the appearance portion of a gun state on the server.

        appearance currently is an opaque dict so the client schema can evolve
        independently; the server only requires it to be a dict.
        """
        pass
        if not isinstance(itemName, str) or not isGunItemName(itemName) \
                or not isinstance(appearance, dict):
            return {
                'ok': False,
                'code': 'BAD_REQUEST',
                'uid': '',
                'state': None,
            }

        uid, state = self._resolveRequestedState(playerId, itemName, extraId)
        if uid is None:
            return state

        if extraId and extraId != uid:
            # Client may be stale; still write to the actual carried uid.
            pass

        state['appearance'] = copy.deepcopy(appearance)
        view = getOrCreateGunStorage(uid, itemName)
        view.set(uid, copy.deepcopy(state))

        result = {
            'ok': True,
            'code': 'OK',
            'uid': uid,
            'state': state,
        }
        pass
        return result

    @Remote
    def setAmmoCount(self, playerId, itemName, extraId, ammoCount):
        # type: (str, str, str, int) -> dict
        """Persist the current magazine ammo count for a gun."""
        pass
        if (
                not isinstance(itemName, str)
                or not isGunItemName(itemName)
                or not isinstance(ammoCount, (int, long))
                or isinstance(ammoCount, bool)
        ):
            return {
                'ok': False,
                'code': 'BAD_REQUEST',
                'uid': '',
                'state': None,
            }

        uid, state = self._resolveRequestedState(playerId, itemName, extraId)
        if uid is None:
            return state

        if extraId and extraId != uid:
            # Client may be stale; still write to the actual carried uid.
            pass

        state['ammoCount'] = max(0, int(ammoCount))
        view = getOrCreateGunStorage(uid, itemName)
        view.set(uid, copy.deepcopy(state))

        result = {
            'ok': True,
            'code': 'OK',
            'uid': uid,
            'state': state,
        }
        pass
        return result
    @Remote
    def setAttachments(self, playerId, itemName, extraId, attachments, appearance=None):
        # type: (str, str, str, dict, dict | None) -> dict
        """Persist attachment map (and optionally appearance) for a gun."""
        pass
        if (
                not isinstance(itemName, str)
                or not isGunItemName(itemName)
                or not isinstance(attachments, dict)
        ):
            return {
                'ok': False,
                'code': 'BAD_REQUEST',
                'uid': '',
                'state': None,
            }

        # Keep only simple slotId -> attachmentId string pairs.
        clean = {}
        for slotId, attachmentId in attachments.items():
            if isinstance(slotId, str) and isinstance(attachmentId, str):
                clean[slotId] = attachmentId

        uid, state = self._resolveRequestedState(playerId, itemName, extraId)
        if uid is None:
            return state

        state['attachments'] = clean
        if appearance is not None:
            if not isinstance(appearance, dict):
                return {
                    'ok': False,
                    'code': 'BAD_REQUEST',
                    'uid': '',
                    'state': None,
                }
        state['appearance'] = copy.deepcopy(appearance)
        view = getOrCreateGunStorage(uid, itemName)
        view.set(uid, copy.deepcopy(state))

        result = {
            'ok': True,
            'code': 'OK',
            'uid': uid,
            'state': state,
        }
        pass
        return result
