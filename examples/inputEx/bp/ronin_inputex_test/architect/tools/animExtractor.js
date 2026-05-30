const fs = require('fs')
const path = require('path')

const moduleDir = path.resolve(__dirname, '../../../../')
const { findManifest, findResDir } = require('./utils')


function walkDir(dir, callback) {
    fs.readdirSync(dir).forEach((file) => {
        const filePath = path.join(dir, file)
        if (fs.statSync(filePath).isDirectory()) {
            walkDir(filePath, callback)
        } else {
            callback(filePath)
        }
    })
}


function findAnimResources(resDir, consumer) {
    const animDir = path.join(resDir, 'animations')
    walkDir(animDir, filePath => {
        if (path.extname(filePath) != '.json') {
            return
        }

        const anim = JSON.parse(fs.readFileSync(filePath, 'utf8'))
        consumer(anim)
    })
}


/**
 * 
 * @param {Record<string, string[]>} animMeta 
 * @param {Record<string, string>[]} timeline 
 * @returns 
 */
function handleExtraData(animMeta, timeline) {
    if (!timeline) {
        return
    }

    animMeta.notifies = {}
    animMeta.extra = {}
    for (const [ time, expr ] of Object.entries(timeline)) {
        const notifies = []
        const extra = {}
        const exprStr = Array.isArray(expr) ? expr.join('') : expr
        for (const equalExpr of exprStr.slice(0, -1).replaceAll(' ', '').split(';')) {
            const [ key, value ] = equalExpr.split('=')
            const variableName = key.replace('v.', '').replace('variable.', '')
            if (variableName.startsWith('notify_')) {
                const notifyName = variableName.slice(7)
                notifies.push({
                    name: notifyName,
                    state: Math.round(value)
                })
            }
            if (variableName.startsWith('data_')) {
                const dataName = variableName.slice(5)
                extra[dataName] = value
            }
        }
        if (notifies.length > 0) {
            animMeta.notifies[time] = notifies
        }
        if (Object.keys(extra).length > 0) {
            animMeta.extra[time] = extra
        }
    }
}


function extractAnimations() {
    const resDir = findResDir()
    if (!resDir) {
        console.error('Cannot find resources directory')
        return
    }

    const animMetaPath = path.join(__dirname, '../../assets/animMeta.py')
    const animMetaInfos = {}

    if (fs.existsSync(animMetaPath)) {
        const existedMeta = JSON.parse(
            fs.readFileSync(animMetaPath).toString()
                .replace('AnimMeta = ', '')
                .replaceAll('True', 'true')
                .replaceAll('False', 'false')
            )
        for (const [ key, value ] of Object.entries(existedMeta)) {
            animMetaInfos[key] = value
        }
    }

    const animKeys = []

    // Merge anim resources
    findAnimResources(resDir, ({ animations }) => {
        for (const [ key, { loop, animation_length, timeline } ] of Object.entries(animations)) {
            const metaInfo = {
                loop: loop ?? false,
                length: animation_length ?? -1,
            }
            handleExtraData(metaInfo, timeline)
            animMetaInfos[key] = metaInfo
            if (animKeys.includes(key)) {
                console.error(`Conflict animations: ${key}`)
            }
            animKeys.push(key)
        }
    })

    fs.writeFileSync(
        animMetaPath,
        `AnimMeta = ${JSON.stringify(animMetaInfos, null, 4)}`
            .replaceAll('true', 'True')
            .replaceAll('false', 'False')
    )


    console.log('Extracted animations:', animKeys.length)
}

extractAnimations()