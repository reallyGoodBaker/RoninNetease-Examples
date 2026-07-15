#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RoninNetease 项目脚手架生成器
生成基于 template / anim / inputEx 三种模式的项目结构
"""

import os
import sys

PROJECT_TYPES = {
    "template": {
        "name": "最小模板（仅 conf + modMain + __init__）",
        "files": {
            "conf.py": '''# -*- coding: utf-8 -*-
MOD_ENGINE_NAME = "engine/architect"
MOD_SYSTEM_NAME = "my_scripts"
MOD_SERVER_MODULES = ["%s" % MOD_SYSTEM_NAME]
MOD_CLIENT_MODULES = ["%s" % MOD_SYSTEM_NAME]
''',
            "modMain.py": '''# -*- coding: utf-8 -*-
from engine.architect.conf import modConf
from engine.architect.compact import createMod, createClient, createServer

modConf().value.name = "myMod"
modConf().value.desc = "My mod description"
modConf().value.author = "author"
''',
            "__init__.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import *
''',
        }
    },
    "inputex": {
        "name": "轻量输入项目（仅客户端 + 输入资产）",
        "files": {
            "conf.py": '''# -*- coding: utf-8 -*-
MOD_ENGINE_NAME = "engine/architect"
MOD_SYSTEM_NAME = "ronin_inputex_test"
MOD_CLIENT_MODULES = ["%s" % MOD_SYSTEM_NAME]
MOD_SERVER_MODULES = ["%s" % MOD_SYSTEM_NAME]

PLUGINS = ["engine.architect.plugins.input"]
''',
            "modMain.py": '''# -*- coding: utf-8 -*-
from engine.architect.conf import modConf
from engine.architect.compact import createMod

modConf().value.name = "inputEx"
modConf().value.desc = "input test"
modConf().value.author = "author"
''',
            "__init__.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import *
from engine.architect.core.annotation import SubsystemClient

@SubsystemClient()
def cs(view):
    view.reg("testClient")
''',
            "testClient.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import ClientSubsystem

class TestClient(ClientSubsystem):
    def __init__(self):
        ClientSubsystem.__init__(self)
        self.name = "testClient"
        self.phase = "Update"

    def init(self, view):
        pass

    def update(self, view):
        pass
''',
            "assets/__init__.py": "",
            "assets/inputAction.py": '''# -*- coding: utf-8 -*-
class InputActions(object):
    ACTION_JUMP = "action_jump"
    ACTION_ATTACK = "action_attack"
''',
            "assets/inputMapping.py": '''# -*- coding: utf-8 -*-
class InputMapping(object):
    def register(self, input_component):
        pass
''',
        }
    },
    "anim": {
        "name": "完整项目（双端 + 动画 + 输入 + 事件）",
        "files": {
            "conf.py": '''# -*- coding: utf-8 -*-
MOD_ENGINE_NAME = "engine/architect"
MOD_SYSTEM_NAME = "my_scripts"
MOD_SERVER_MODULES = ["%s" % MOD_SYSTEM_NAME]
MOD_CLIENT_MODULES = ["%s" % MOD_SYSTEM_NAME]

PLUGINS = [
    "engine.architect.plugins.animation",
    "engine.architect.plugins.input",
]
''',
            "modMain.py": '''# -*- coding: utf-8 -*-
from engine.architect.conf import modConf
from engine.architect.compact import createMod

modConf().value.name = "animDemo"
modConf().value.desc = "animation demo"
modConf().value.author = "author"
''',
            "__init__.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import *
from engine.architect.core.annotation import SubsystemServer, SubsystemClient

@SubsystemClient()
def cs(view):
    view.reg("systems.animPlayer")

@SubsystemServer()
def ss(view):
    view.reg("systems.animServer")
''',
            "client.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import createClient
createClient()
''',
            "server.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import createServer
createServer()
''',
            "assets/__init__.py": "",
            "assets/animations.py": '''# -*- coding: utf-8 -*-
from engine.architect.core.asset import Asset

class Animations(Asset):
    def __init__(self):
        self.id = None
        self.key_frame = None
        self.duration = 0.0

    def serialize(self):
        return {"id": self.id, "key_frame": self.key_frame, "duration": self.duration}
''',
            "assets/animMeta.py": '''# -*- coding: utf-8 -*-
from engine.architect.core.asset import Asset

class AnimMeta(Asset):
    def __init__(self):
        self.name = ""
        self.type = ""

    def serialize(self):
        return {"name": self.name, "type": self.type}
''',
            "assets/inputAction.py": '''# -*- coding: utf-8 -*-
class InputActions(object):
    ACTION_JUMP = "action_jump"
    ACTION_ATTACK = "action_attack"
''',
            "assets/inputMapping.py": '''# -*- coding: utf-8 -*-
class InputMapping(object):
    def register(self, input_component):
        pass
''',
            "assets/notifies.py": '''# -*- coding: utf-8 -*-
class Notifies(object):
    ANIM_FINISH = "AnimFinishNotify"
    PLAYER_JOIN = "PlayerJoinNotify"
''',
            "systems/__init__.py": "",
            "systems/animPlayer.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import ClientSubsystem

class AnimPlayerSystem(ClientSubsystem):
    def __init__(self):
        ClientSubsystem.__init__(self)
        self.name = "animPlayer"
        self.phase = "Update"

    def init(self, view):
        pass

    def update(self, view):
        pass

    def destroy(self, view):
        pass
''',
            "systems/animServer.py": '''# -*- coding: utf-8 -*-
from engine.architect.compact import ServerSubsystem

class AnimServerSystem(ServerSubsystem):
    def __init__(self):
        ServerSubsystem.__init__(self)
        self.name = "animServer"

    def init(self, view):
        pass

    def update(self, view):
        pass
''',
            "components/__init__.py": "",
        }
    }
}


def generate(project_type, output_dir):
    if project_type not in PROJECT_TYPES:
        print("Supported types: %s" % ", ".join(PROJECT_TYPES.keys()))
        return False

    spec = PROJECT_TYPES[project_type]
    base = os.path.join(output_dir, project_type)

    for rel_path, content in spec["files"].items():
        full_path = os.path.join(base, rel_path)
        dir_name = os.path.dirname(full_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(full_path, "wb") as f:
            f.write(content.encode("utf-8"))
        print("  Created: %s" % full_path)

    print("\n✅ Project '%s' generated at: %s" % (project_type, base))
    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scaffold.py <type> <output_dir>")
        print("  types: %s" % ", ".join(PROJECT_TYPES.keys()))
        sys.exit(1)

    generate(sys.argv[1], sys.argv[2])
