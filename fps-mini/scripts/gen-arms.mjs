#!/usr/bin/env node
/**
 * gen-arms.mjs — 由第一人称武器模型 (rifle) 生成 / 更新配套的 arms 模型
 *
 * 背景
 *   第一人称下武器和手臂是两个独立的 geometry:
 *     - rifle 模型 (geometry.ww1.xxx)  由 controller.render.template.weapon 渲染
 *     - arms  模型 (geometry.arms.xxx) 由 controller.render.first_person.arm 渲染
 *   两边靠同名的 fpsrightarm / fpsrightsleeve / fpsleftarm / fpsleftsleeve
 *   以及 fpsroot -> control -> crosshair -> center 这条父链对齐。
 *
 *   手臂的 cube 贴图必须用 arms 自己的 UV (arms 走 texture.default = 玩家皮肤),
 *   不能带 rifle 的 UV (rifle 走 texture.weapon = 武器贴图)。
 *
 * 做法
 *   1. 从 rifle 模型取手臂骨骼: pivot / rotation / cube 的 origin、size、inflate
 *   2. 每根 cube 的 uv 保留 arms 基底里的值 (不覆盖)
 *   3. 默认同时同步父链 fpsroot / control / crosshair / center
 *      (这几根会被动画旋转, 轴心不一致时手臂会在走路/奔跑/开枪时和枪错位)
 *   4. 其余骨骼、description、identifier、贴图尺寸全部保留 arms 基底
 *
 * 注意
 *   rifle 是唯一数据源: arms 文件里除 uv 之外的手工改动都会被覆盖。
 *   每次动手之前先跑 --dry 看一眼改动清单。
 *
 * 用法
 *   node scripts/gen-arms.mjs ross_mk3                     # 生成/更新一把
 *   node scripts/gen-arms.mjs ross_mk3 gew98               # 多把
 *   node scripts/gen-arms.mjs --all                        # 全部 (跳过 template)
 *   node scripts/gen-arms.mjs --all --dry                  # 只看会改什么, 不写
 *   node scripts/gen-arms.mjs --all --check                # CI 用: 有文件过期则以 1 退出
 *   node scripts/gen-arms.mjs ross_mk3 --no-chain          # 只同步手臂, 不同步父链
 *   node scripts/gen-arms.mjs newgun --out /tmp/arms.json  # 写到别处 (试跑)
 *
 * 选项
 *   --all            处理 rifle 目录下所有模型 (跳过 template*)
 *   --dry            只打印改动, 不写文件
 *   --check          同 --dry, 但有文件需要更新时 exit 1
 *   --no-chain       不同步 fpsroot/control/crosshair/center
 *   --out <file>     输出到指定文件 (只允许单把武器)
 *   --template <f>   arms 文件不存在时用的基底模板 (默认 rp/models/entity/arms.geo.json)
 *   --rifle-dir <d>  rifle 模型目录
 *   --arms-dir <d>   arms 模型目录
 *   --quiet          只输出汇总
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');
const DEFAULT_RIFLE_DIR = path.join(ROOT, 'rp', 'models', 'entity', 'rifles', 'first_person');
const DEFAULT_ARMS_DIR = path.join(ROOT, 'rp', 'models', 'entity', 'arms');
const DEFAULT_TEMPLATE = path.join(ROOT, 'rp', 'models', 'entity', 'arms.geo.json');

/** 必须从 rifle 复制的手臂骨骼 */
const ARM_BONES = ['fpsrightarm', 'fpsrightsleeve', 'fpsleftarm', 'fpsleftsleeve'];
/** 手臂的挂载父链, 会被动画旋转, 轴心必须和 rifle 一致 */
const CHAIN_BONES = ['fpsroot', 'control', 'crosshair', 'center'];
/** --all 时跳过的模型 */
const SKIP_ALL = [/^template/i];
/** 输出里忽略的字段 (只影响展示, 不影响生成结果) */
const NOISY_KEYS = new Set(['name']);

function rel(p) {
  const r = path.relative(ROOT, p);
  return r.startsWith('.') ? p : r.split(path.sep).join('/');
}

function parseArgs(argv) {
  const o = {
    weapons: [], all: false, dry: false, check: false, chain: true, quiet: false,
    out: null, template: DEFAULT_TEMPLATE, rifleDir: DEFAULT_RIFLE_DIR, armsDir: DEFAULT_ARMS_DIR,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const val = () => {
      if (i + 1 >= argv.length) throw new Error('选项 ' + a + ' 缺少参数');
      return argv[++i];
    };
    if (a === '-h' || a === '--help') o.help = true;
    else if (a === '--all') o.all = true;
    else if (a === '--dry') o.dry = true;
    else if (a === '--check') o.check = true;
    else if (a === '--no-chain') o.chain = false;
    else if (a === '--quiet') o.quiet = true;
    else if (a === '--out') o.out = val();
    else if (a === '--template') o.template = path.resolve(val());
    else if (a === '--rifle-dir') o.rifleDir = path.resolve(val());
    else if (a === '--arms-dir') o.armsDir = path.resolve(val());
    else if (a.startsWith('-')) throw new Error('未知选项: ' + a);
    else o.weapons.push(a);
  }
  return o;
}

function readText(p) {
  return fs.readFileSync(p, 'utf8');
}

function readJson(p) {
  try {
    return JSON.parse(readText(p));
  } catch (e) {
    throw new Error('解析失败 ' + rel(p) + ': ' + e.message);
  }
}

function findModel(dir, name) {
  for (const f of [name + '.geo.json', name + '.json']) {
    const p = path.join(dir, f);
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function firstGeometry(doc, file) {
  const g = doc['minecraft:geometry'];
  if (!Array.isArray(g) || !g.length) throw new Error(rel(file) + ': 缺少 minecraft:geometry[0]');
  return g[0];
}

function indexBones(geo) {
  const m = new Map();
  for (const b of geo.bones || []) {
    if (b && typeof b.name === 'string' && !m.has(b.name)) m.set(b.name, b);
  }
  return m;
}

function withoutKey(obj, key) {
  const out = {};
  for (const k of Object.keys(obj)) if (k !== key) out[k] = obj[k];
  return out;
}

/** 按 base 的键顺序输出、值取 source; base 没有的键按 source 顺序补在末尾 */
function mergeShallow(base, source) {
  const out = {};
  const taken = new Set();
  if (base) {
    for (const k of Object.keys(base)) {
      if (Object.prototype.hasOwnProperty.call(source, k)) {
        out[k] = source[k];
        taken.add(k);
      }
    }
  }
  for (const k of Object.keys(source)) if (!taken.has(k)) out[k] = source[k];
  return out;
}

/**
 * 合并一根骨骼:
 *   除 cubes 外的字段全部以 rifle 为准 (pivot / rotation / parent ...)
 *   每根 cube 的字段以 rifle 为准, 但 uv 保留 base(arms) 的
 */
function mergeBone(baseBone, rifleBone, ctx, name) {
  const out = mergeShallow(
    baseBone ? withoutKey(baseBone, 'cubes') : null,
    withoutKey(rifleBone, 'cubes')
  );
  const rifleCubes = rifleBone.cubes || [];
  const baseCubes = (baseBone && baseBone.cubes) || [];
  if (!rifleCubes.length && baseCubes.length) {
    ctx.warnings.push(name + ': rifle 该骨骼没有 cube, 保留 arms 的 cube (只更新 pivot/rotation)');
    out.cubes = baseCubes;
    return out;
  }
  if (baseBone && baseCubes.length && baseCubes.length !== rifleCubes.length) {
    ctx.warnings.push(name + ': cube 数量不一致 (arms ' + baseCubes.length + ' / rifle ' + rifleCubes.length + ')');
  }
  out.cubes = rifleCubes.map((rc, i) => {
    const bc = baseCubes[i];
    const c = mergeShallow(bc, rc);
    if (bc && bc.uv) {
      c.uv = bc.uv;                       // <- arms 的 UV, 不覆盖
    } else if (rc.uv) {
      ctx.warnings.push(name + '.cubes[' + i + ']: 基底没有 uv, 退回用 rifle 的 uv');
    }
    return c;
  });
  return out;
}

function fmt(v) {
  if (v === undefined) return '(无)';
  return JSON.stringify(v);
}

function cubeSummary(cubes) {
  return (cubes || []).map((c) => 'origin=' + fmt(c.origin) + ' size=' + fmt(c.size)).join(' ');
}

/** 返回人话的字段差异列表 */
function diffBone(before, after) {
  const out = [];
  const keys = new Set([...Object.keys(before || {}), ...Object.keys(after || {})]);
  for (const k of keys) {
    const a = before ? before[k] : undefined;
    const b = after[k];
    if (JSON.stringify(a) === JSON.stringify(b)) continue;
    if (NOISY_KEYS.has(k)) continue;
    if (k === 'cubes') {
      const ba = (before && before.cubes) || [];
      const bb = (after && after.cubes) || [];
      if (ba.length !== bb.length) {
        out.push('cubes ' + ba.length + ' -> ' + bb.length);
      } else {
        const strip = (c) => {
          const o = {};
          for (const kk of Object.keys(c)) if (kk !== 'uv') o[kk] = c[kk];
          return o;
        };
        let geoChanged = false;
        let uvChanged = false;
        for (let i = 0; i < bb.length; i++) {
          if (JSON.stringify(strip(ba[i])) !== JSON.stringify(strip(bb[i]))) geoChanged = true;
          if (JSON.stringify(ba[i].uv) !== JSON.stringify(bb[i].uv)) uvChanged = true;
        }
        if (geoChanged) out.push('cubes ' + cubeSummary(bb));
        if (uvChanged) out.push('!! uv 被改动 (不应该发生)');
      }
    } else {
      out.push(k + ' ' + fmt(a) + ' -> ' + fmt(b));
    }
  }
  return out;
}

function generate(opts, weapon) {
  const riflePath = findModel(opts.rifleDir, weapon);
  if (!riflePath) throw new Error(weapon + ': 找不到 rifle 模型 (' + rel(opts.rifleDir) + ')');
  const armsPath = findModel(opts.armsDir, weapon);

  // 该武器还没有自己的 arms 模型 -> 以模板为基底新建 (identifier 要改成 geometry.arms.<weapon>)
  const creating = !armsPath;
  const targetPath = opts.out
    ? path.resolve(opts.out)
    : (armsPath || path.join(opts.armsDir, weapon + '.geo.json'));

  const rifleGeo = firstGeometry(readJson(riflePath), riflePath);
  const basePath = armsPath || opts.template;
  const baseText = readText(basePath);
  const doc = JSON.parse(baseText);
  const geo = firstGeometry(doc, basePath);
  if (creating) {
    geo.description = Object.assign({}, geo.description, { identifier: 'geometry.arms.' + weapon });
  }

  const ctx = { warnings: [] };
  const rifleBones = indexBones(rifleGeo);
  const outBones = indexBones(geo);
  const want = ARM_BONES.concat(opts.chain ? CHAIN_BONES : []);
  const changes = [];
  const seen = new Set();

  for (const name of want) {
    if (seen.has(name)) continue;
    seen.add(name);
    const rb = rifleBones.get(name);
    if (!rb) {
      if (ARM_BONES.indexOf(name) >= 0) {
        throw new Error(weapon + ': rifle 模型缺少手臂骨骼 ' + name + ' (' + rel(riflePath) + ')');
      }
      continue; // 父链缺某根就跳过
    }
    const bb = outBones.get(name);
    const merged = mergeBone(bb, rb, ctx, name);
    if (!bb) {
      geo.bones.push(merged);
      outBones.set(name, merged);
      changes.push({ name, fields: ['新增骨骼'], arm: ARM_BONES.indexOf(name) >= 0 });
      continue;
    }
    const fields = diffBone(bb, merged);
    if (!fields.length) continue;
    geo.bones[geo.bones.indexOf(bb)] = merged;
    outBones.set(name, merged);
    changes.push({ name, fields, arm: ARM_BONES.indexOf(name) >= 0 });
  }

  const text = JSON.stringify(doc) + (/\n$/.test(baseText) ? '\n' : '');
  const previous = fs.existsSync(targetPath) ? readText(targetPath) : null;

  return {
    weapon, riflePath, armsPath, basePath, targetPath, creating,
    changed: previous !== text, text, previous, changes, warnings: ctx.warnings,
  };
}

function report(r, opts) {
  const tag = r.changed ? (r.previous === null ? '新建' : '更新') : '无变化';
  console.log(r.weapon + '  [' + tag + ']');
  if (!opts.quiet) {
    console.log('  rifle : ' + rel(r.riflePath));
    console.log('  arms  : ' + rel(r.targetPath) + (r.creating ? '  (由 ' + rel(r.basePath) + ' 新建)' : ''));
  }
  if (!r.changed) return;
  const armN = r.changes.filter((c) => c.arm).length;
  const chainN = r.changes.length - armN;
  console.log('  改动: 手臂 ' + armN + ' 根, 父链 ' + chainN + ' 根' + (opts.chain ? '' : '  [--no-chain]'));
  if (!opts.quiet) {
    for (const c of r.changes) {
      console.log('    ' + c.name.padEnd(16) + c.fields.join('  |  '));
    }
    if (armN) console.log('    uv: 全部保留 arms 基底的 UV');
  }
  for (const w of r.warnings) console.log('    ! ' + w);
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    const src = fs.readFileSync(__filename, 'utf8');
    const m = /\/\*\*([\s\S]*?)\*\//.exec(src);
    console.log(m ? m[1].replace(/^\s*\*[ 	]?/gm, '').replace(/\s+$/, '') : '用法: node scripts/gen-arms.mjs <weapon...> [--all] [--dry] [--check]');
    return 0;
  }

  let weapons = opts.weapons.slice();
  if (opts.all) {
    if (opts.out) throw new Error('--out 不能和 --all 一起用');
    for (const f of fs.readdirSync(opts.rifleDir)) {
      const m = /^(.*)\.(geo\.)?json$/i.exec(f);
      if (!m) continue;
      const name = m[1].replace(/\.geo$/i, '');   // sniper.geo.json -> sniper
      if (SKIP_ALL.some((re) => re.test(name))) continue;
      weapons.push(name);
    }
  }
  weapons = [...new Set(weapons)];
  if (!weapons.length) throw new Error('没有指定武器。用法: node scripts/gen-arms.mjs <weapon> [--all] [--dry]');

  let stale = 0;
  let failed = 0;
  const results = [];
  for (const w of weapons) {
    try {
      const r = generate(opts, w);
      results.push(r);
      report(r, opts);
      if (r.changed) {
        stale++;
        if (!opts.dry && !opts.check) {
          fs.mkdirSync(path.dirname(r.targetPath), { recursive: true });
          fs.writeFileSync(r.targetPath, r.text);
        }
      }
    } catch (e) {
      failed++;
      console.error(w + '  [错误] ' + e.message);
    }
  }

  const written = opts.dry || opts.check ? 0 : results.filter((r) => r.changed).length;
  console.log('');
  console.log('共 ' + weapons.length + ' 把: 改动 ' + stale + ', 已写入 ' + written +
    (failed ? ', 失败 ' + failed : '') + (opts.chain ? '' : '   [父链未同步]'));
  if (opts.dry) console.log('(--dry 模式, 未写入任何文件)');
  if (opts.check && stale) console.log('(--check: 有文件需要更新)');
  return failed ? 1 : (opts.check && stale ? 1 : 0);
}

try {
  process.exit(main());
} catch (e) {
  console.error('错误: ' + e.message);
  process.exit(1);
}
