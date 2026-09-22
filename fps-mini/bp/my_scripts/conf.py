# -*- coding: utf-8 -*-

MOD_NAME = 'my_mod'
MOD_VERSION = '1.0.0'

MOD_ENGINE_NAME = 'engine'
MOD_SYSTEM_NAME = 'system'

# Shared weapon item -> weapon asset mapping.
# This is the single source used by both client and server sync code.
GUN_ITEM_NAMES = {
    # 'roninexample:pistol': 'pistol',
    # 'roninexample:bolt': 'bolt',
    # 'roninexample:sniper': 'sniper',
    # 'roninexample:auto': 'auto',
    'ww1:smle_mk3': 'smle_mk3',
    'ww1:ross_mk3': 'ross_mk3',
    'ww1:gewehr98': 'gewehr98',
    'ww1:berthier_m1916': 'berthier_m1916',
    'ww1:carcano_m1891': 'carcano_m1891',
    'ww1:gewehr_m95': 'gewehr_m95',
    'ww1:mosin_nagant': 'mosin_nagant',
}

# Allow GUN_ITEM_NAMES to be changed at runtime via modConf().set(...).
HOT_RELOADABLE = ['GUN_ITEM_NAMES']

# DEBUG = True

MOD_SERVER_MODULES = [
    'lib.serverAuth',
    'lib.renderServer',
    'lib.gunServerSync',
    'lib.droppedWeapon',
]
MOD_CLIENT_MODULES = [
    'assets.notifies.__all__',
    'assets.attachments.__all__',
    'assets.inputActions.__all__',
    'assets.inputMappings.__all__',
    'features.__all__',

    'systems.playerInit',
    'lib.gunClientSync',
    'lib.droppedWeaponClient',
]

PLUGINS = [
    '$vendor.animation',
    '$vendor.motion',
    '$vendor.input',

    '$user.default_indicator',
]