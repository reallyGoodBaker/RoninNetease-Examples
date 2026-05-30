const fs = require('fs')
const path = require('path')

const moduleDir = path.resolve(__dirname, '../../../../')

function findResDir() {
    for (const dir of fs.readdirSync(moduleDir)) {
        const filePath = path.join(moduleDir, dir)
        if (fs.statSync(filePath).isDirectory()) {
            const manifest = findManifest(filePath, 'resources')
            if (manifest) {
                return manifest
            }
        }
    }
}

function findDataDir() {
    for (const dir of fs.readdirSync(moduleDir)) {
        const filePath = path.join(moduleDir, dir)
        if (fs.statSync(filePath).isDirectory()) {
            const manifest = findManifest(filePath, 'data')
            if (manifest) {
                return manifest
            }
        }
    }
}

/**
 * @param {string} filePath 
 * @param {'resources'|'data'} moduleType 
 * @returns 
 */
function findManifest(filePath, moduleType) {
    const manifestPath = path.join(filePath, 'manifest.json')
    if (!fs.existsSync(manifestPath)) {
        return
    }

    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
    for (const { type } of manifest.modules) {
        if (type === moduleType) {
            return filePath
        }
    }
}

module.exports = {
    findResDir,
    findManifest,
}