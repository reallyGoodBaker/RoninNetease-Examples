# -*- coding: utf-8 -*-
from mod.common.mod import Mod
from .engine.architect.startup import createServer, createClient, conf


@Mod.Binding(name = conf('MOD_NAME'), version = conf('MOD_VERSION'))
class ModBase(object):
    @Mod.InitServer()
    def initServer(self):
        createServer()

    @Mod.InitClient()
    def initClient(self):
        createClient()