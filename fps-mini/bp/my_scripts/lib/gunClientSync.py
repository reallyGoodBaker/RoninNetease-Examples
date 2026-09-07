# -*- coding: utf-8 -*-
"""Client-side gun state sync.

The client keeps a lightweight canonical copy of the currently carried gun's
server-stored state. The full state is never rebuilt from itemDict; it is always
fetched from GunServerSyncSystem when the carried item changes.
"""
import copy

from ..engine.architect.compact import (
    ClientSubsystem, SubsystemClient,
    EventListener, events,
    compClient, localPlayerId, remote,
)
from .gunSync import isGunItemName, itemNameOf
from .shooter import ShooterSystem


@SubsystemClient
class GunClientSyncSystem(ClientSubsystem):
    """Canonical server state cache for the locally carried weapon."""

    def onInit(self):
        # type: () -> None
        pass
        self.canonicalState = None
        self.canonicalUid = ''
        self.canonicalItemName = None
        self._requestToken = 0
        self._requesting = False
        pass

    def onDestroy(self):
        # type: () -> None
        self._resetCanonical()

    def resetForWorld(self):
        # type: () -> None
        """Drop all client-side cached state when entering a fresh world/save."""
        self._resetCanonical()

    def syncCurrentCarried(self):
        # type: () -> None
        """Reset cache and fetch state for the currently carried item."""
        self.resetForWorld()
        itemComp = compClient.CreateItem(localPlayerId())
        try:
            itemDict = itemComp.GetCarriedItem()
        except Exception as errorObject:
            pass
            return
        self._handleCarriedItem(itemDict)

    # ---------------------------------------------------------------
    # Public accessors
    # ---------------------------------------------------------------

    def getCanonicalState(self):
        # type: () -> dict | None
        return copy.deepcopy(self.canonicalState)

    def getAppearance(self):
        # type: () -> dict
        if not self.canonicalState \
                or not isinstance(self.canonicalState.get('appearance'), dict):
            return {}
        return copy.deepcopy(self.canonicalState['appearance'])

    def getCurrentUid(self):
        # type: () -> str
        return self.canonicalUid

    # ---------------------------------------------------------------
    # Carried item tracking
    # ---------------------------------------------------------------

    def _resetCanonical(self):
        # type: () -> None
        self._requestToken += 1
        self.canonicalState = None
        self.canonicalUid = ''
        self.canonicalItemName = None
        self._requesting = False

    def _handleCarriedItem(self, itemDict):
        # type: (dict | None) -> None
        itemName = itemNameOf(itemDict)
        if not isGunItemName(itemName):
            self._resetCanonical()
            return

        self._requestToken += 1
        token = self._requestToken
        self._requesting = True
        extraId = (itemDict or {}).get('extraId') or ''

        pass
        try:
            future = remote.client.invoke(
                'GunServerSyncSystem.ensureGunState',
                itemName,
                extraId,
            )
        except Exception as errorObject:
            pass
            self._requesting = False
            return

        future.done(
            lambda result, t=token: self._onStateResult(t, result)
        )
        future.expected(
            lambda error, t=token: self._onStateError(t, error)
        )

    def _onStateResult(self, token, result):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        self._requesting = False
        if not isinstance(result, dict) or not result.get('ok'):
            code = result.get('code') if isinstance(result, dict) else 'ERROR'
            pass
            return

        state = result.get('state')
        if not isinstance(state, dict):
            pass
            return

        self.canonicalState = copy.deepcopy(state)
        self.canonicalUid = result.get('uid') or ''
        self.canonicalItemName = state.get('itemName')
        self._applyToShooter()
        pass

    def _onStateError(self, token, error):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        self._requesting = False
        pass

    def _applyToShooter(self):
        # type: () -> None
        """Push the freshly fetched server state into the active weapon."""
        if not self.canonicalState:
            return
        shooter = ShooterSystem.getInstance()
        if shooter is not None:
            shooter.applyServerGunState(self.canonicalState, self.canonicalUid)

    # ---------------------------------------------------------------
    # Mutations
    # ---------------------------------------------------------------

    def requestSetAppearance(self, appearance):
        # type: (dict) -> object | None
        """Persist an appearance dict for the currently carried gun."""
        if not self.canonicalState or not self.canonicalUid:
            return None
        itemName = self.canonicalState.get('itemName')
        if not itemName:
            return None

        token = self._requestToken
        try:
            future = remote.client.invoke(
                'GunServerSyncSystem.setAppearance',
                itemName,
                self.canonicalUid,
                appearance,
            )
        except Exception as errorObject:
            pass
            return None

        future.done(
            lambda result, t=token: self._onAppearanceResult(t, result)
        )
        future.expected(
            lambda error, t=token: self._onAppearanceError(t, error)
        )
        return future

    def requestSetAmmoCount(self, ammoCount):
        # type: (int) -> object | None
        """Persist the current magazine ammo count for the carried gun."""
        if not self.canonicalState or not self.canonicalUid:
            return None
        itemName = self.canonicalState.get('itemName')
        if not itemName:
            return None

        token = self._requestToken
        try:
            future = remote.client.invoke(
                'GunServerSyncSystem.setAmmoCount',
                itemName,
                self.canonicalUid,
                int(ammoCount),
            )
        except Exception as errorObject:
            pass
            return None

        future.done(
            lambda result, t=token: self._onAmmoResult(t, result)
        )
        future.expected(
            lambda error, t=token: self._onAmmoError(t, error)
        )
        return future

    def _onAmmoResult(self, token, result):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        if not isinstance(result, dict) or not result.get('ok'):
            pass
            return
        state = result.get('state')
        if isinstance(state, dict):
            self.canonicalState = copy.deepcopy(state)
        pass

    def _onAmmoError(self, token, error):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        pass

    def requestSetAttachments(self, attachments, appearance=None):
        # type: (dict, dict | None) -> object | None
        """Persist attachment map and appearance together on the server."""
        if not self.canonicalState or not self.canonicalUid:
            return None
        itemName = self.canonicalState.get('itemName')
        if not itemName:
            return None

        token = self._requestToken
        try:
            future = remote.client.invoke(
                'GunServerSyncSystem.setAttachments',
                itemName,
                self.canonicalUid,
                attachments,
                appearance,
            )
        except Exception as errorObject:
            pass
            return None

        future.done(
            lambda result, t=token: self._onAttachmentsResult(t, result)
        )
        future.expected(
            lambda error, t=token: self._onAttachmentsError(t, error)
        )
        return future

    def _onAttachmentsResult(self, token, result):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        if not isinstance(result, dict) or not result.get('ok'):
            pass
            return
        state = result.get('state')
        if isinstance(state, dict):
            self.canonicalState = copy.deepcopy(state)
        pass

    def _onAttachmentsError(self, token, error):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        pass

    def _onAppearanceResult(self, token, result):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        if not isinstance(result, dict) or not result.get('ok'):
            return
        state = result.get('state')
        if isinstance(state, dict):
            self.canonicalState = copy.deepcopy(state)

    def _onAppearanceError(self, token, error):
        # type: (int, object) -> None
        if token != self._requestToken:
            return
        pass

    # ---------------------------------------------------------------
    # Events
    # ---------------------------------------------------------------

    # World-load sync is driven by PlayerShooterInitSystem so cache reset and
    # weapon hiding happen in a deterministic order.

    # Carried item sync is driven by PlayerShooterInitSystem.
