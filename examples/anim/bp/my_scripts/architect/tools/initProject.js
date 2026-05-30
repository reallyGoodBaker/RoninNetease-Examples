const fs = require('fs')
const path = require('path')


const modMainCode = `# -*- coding: utf-8 -*-
from mod.common.mod import Mod
from .architect.startup import createServer, createClient, conf


@Mod.Binding(name = conf('MOD_NAME'), version = conf('MOD_VERSION'))
class ModBase(object):
    @Mod.InitServer()
    def initServer(self):
        createServer()

    @Mod.InitClient()
    def initClient(self):
        createClient()`


const confCode = `# -*- coding: utf-8 -*-

MOD_NAME = 'my_mod'
MOD_VERSION = '1.0.0'

MOD_ENGINE_NAME = 'engine'
MOD_SYSTEM_NAME = 'system'

MOD_SERVER_MODULES = [
]
MOD_CLIENT_MODULES = [
]

PLUGINS = [

]`


function initProject() {
    const rootDir = path.resolve(__dirname, '../../')
    const assetsDir = path.join(rootDir, 'assets')
    const confFile = path.join(rootDir, 'conf.py')
    const modMainFile = path.join(rootDir, 'modMain.py')

    if (!fs.existsSync(assetsDir)) {
        fs.mkdirSync(assetsDir)
    }

    if (!fs.existsSync(confFile)) {
        fs.writeFileSync(confFile, confCode)
    }

    fs.writeFileSync(modMainFile, modMainCode)
}

initProject()