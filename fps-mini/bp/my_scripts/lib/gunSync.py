# -*- coding: utf-8 -*-
"""Gun server-side storage sync shared helpers.

Strategy:
  * The weapon item's extraId is only an opaque gun uid, NOT the full state.
  * The full gun state (ammo/attachments/appearance) lives in server KV.
  * The client asks the server for this state whenever the carried item changes.
  * Adding/removing fields on the server record is safe: the server is the only
    place that has to know the current schema, the client only renders what it
    receives.
"""

from ..engine.architect.core.configurator import modConf


def itemNameOf(itemDict):
    # type: (dict | None) -> str | None
    """Return the item identifier no matter which key the engine used."""
    if not itemDict:
        return None
    return itemDict.get('itemName') or itemDict.get('newItemName')


def getGunItemNames():
    # type: () -> dict
    """Read the current weapon item mapping through modConf."""
    value = modConf()('GUN_ITEM_NAMES')
    return value if isinstance(value, dict) else {}


def isGunItemName(itemName):
    # type: (str | None) -> bool
    return bool(itemName and itemName in getGunItemNames())


def defaultGunStorage(itemName):
    # type: (str) -> dict
    """New server record for a gun uid.

    appearance is intentionally an empty dict for now. Later it will hold the
    per-skin custom color palette chosen by the player.
    """
    return {
        'version': 1,
        'itemName': itemName,
        'ammoCount': -1,  # -1 means no server memory yet -> full mag
        'attachments': {},
        'appearance': {},
    }
