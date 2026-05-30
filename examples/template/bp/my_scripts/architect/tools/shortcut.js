const fs = require('fs')
const path = require('path')

const rootDir = path.join(__dirname, '../../').replaceAll('\\', '/')

const shortcut = `
const fs = require('fs')
const path = require('path')
const proc = require('child_process')
const rootDir = '${rootDir}'
const args = process.argv.slice(2)

proc.execSync(\`node ./architect/tools/${args[0]} ${args.slice(1).join(' ')}\`)
`