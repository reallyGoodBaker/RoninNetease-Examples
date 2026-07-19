# -*- coding: utf-8 -*-

MOD_NAME = 'my_mod'
MOD_VERSION = '1.0.0'

MOD_ENGINE_NAME = 'engine'
MOD_SYSTEM_NAME = 'system'

DEBUG = True

MOD_SERVER_MODULES = [
    'lib.serverAuth',

    'systems.syncPersona',
]
MOD_CLIENT_MODULES = [
    'assets.notifies.reload',

    # 'systems.playerPersona',
    # 'systems.playerAnim',
    'systems.playerInit'
]

PLUGINS = [
    '$vendor.animation',
]