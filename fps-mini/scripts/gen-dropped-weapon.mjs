#!/usr/bin/env node
/**
 * gen-dropped-weapon.mjs — 生成"丢在地上的枪"用的实体 / 模型 / 摆位动画
 *
 * 背景
 *   枪械物品丢出来是原版 item entity，只会显示 2D 图标。
 *   本脚本为每一把枪生成一套"掉落物实体"，由服务端在掉落时替换原版掉落物：
 *     bp/entities/dropped_weapon/<weapon>.json        实体定义 (物理/碰撞/不掉血)
 *     rp/entity/dropped_weapon/<weapon>.json         客户端实体 (武器模型 + 武器贴图)
 *     rp/animations/dropped_weapon/<weapon>.animation.json
 *                                                    摆位动画 (把模型摆到地上)
 *   另有一份共用的渲染控制器：
 *     rp/render_controllers/dropped_weapon.render.json
 *
 * 数据来源 (单一数据源, 不重复维护)
 *   bp/my_scripts/assets/renderResources/<weapon>.py   -> model / texture
 *   bp/my_scripts/conf.py 的 GUN_ITEM_NAMES            -> 哪些是枪
 *   rp/models 下的 geo 文件                            -> 几何体(算包围盒和摆位)
 *
 * 用法
 *   node scripts/gen-dropped-weapon.mjs                # 只处理 GUN_ITEM_NAMES 里的枪
 *   node scripts/gen-dropped-weapon.mjs --all          # 处理所有有 renderResources 的枪
 *   node scripts/gen-dropped-weapon.mjs ross_mk3       # 指定
 *   node scripts/gen-dropped-weapon.mjs --dry          # 只看会写什么
 *   node scripts/gen-dropped-weapon.mjs --check        # 有文件过期则 exit 1
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// ---- 摆位参数: 想调整掉的枪怎么躺, 改这几行 ----
const LAY_FLAT = true;    // true: 侧躺在地上(绕 Z 轴转 90 度); false: 立着
const SCALE = 'auto';    // 'auto' = 按 TARGET_LENGTH 自动缩放; 也可以直接写数字(1 = 和第一人称里一样大)
const TARGET_LENGTH = 2.2; // auto 时最长边的目标长度(格); 真实步枪约 1.1~1.3, 这是放大后的手感值
const LIFT = 0.0;         // 额外离地高度(格)
// ---------------------------------------------
const ENTITY_PREFIX = 'template:dropped_';
const FAMILY = 'dropped_weapon';
// 渲染直接复用武器自己的渲染控制器 (controller.render.template.weapon 之类):
// 它自带 pbr_tint 材质 + 金属贴图 + part_visibility 里的 v.attach_* 配件开关,
// 掉落物实体这边只要把玩家当前的 v.attach_* / q.mod.tint_color_* 复制过来就行。
const FALLBACK_CONTROLLER = 'controller.render.template.weapon';
// 掉在地上的枪要隐藏的骨骼 (按名字包含的关键字匹配, 不区分大小写)。
// 这些是装填用的道具模型(漏夹/子弹/单发弹), 平时靠动画挪走, 不播动画就会露在原地。
const HIDE_BONE_KEYWORDS = ['clip', 'bullet', 'single'];

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const P = (p) => path.join(ROOT, p);
const DIRS = {
  render: P('bp/my_scripts/assets/renderResources'),
  conf: P('bp/my_scripts/conf.py'),
  models: P('rp/models'),
  bpEntity: P('bp/entities/dropped_weapon'),
  rpEntity: P('rp/entity/dropped_weapon'),
  rpAnim: P('rp/animations/dropped_weapon'),
};

// ---------------------------------------------------------------- utils

function readText(p) {
  return fs.readFileSync(p, 'utf8');
}

/** python 里那种简单 dict 字面量 -> JS 对象 */
function pyLiteral(src) {
  const cleaned = src
    .replace(/^[ \t]*#.*$/gm, '')
    .replace(/\bNone\b/g, 'null')
    .replace(/\bTrue\b/g, 'true')
    .replace(/\bFalse\b/g, 'false')
    .replace(/'/g, '"')
    .replace(/,(\s*[}\]])/g, '$1');
  return JSON.parse(cleaned);
}

function readRenderResource(weapon) {
  const file = path.join(DIRS.render, weapon + '.py');
  if (!fs.existsSync(file)) return null;
  const m = /^Asset\s*=\s*(\{[\s\S]*\})\s*$/m.exec(readText(file));
  if (!m) return null;
  return pyLiteral(m[1]);
}

/** conf.py 里 GUN_ITEM_NAMES 的 value 集合 (= 所有枪) */
function readGunWeapons() {
  const m = /GUN_ITEM_NAMES\s*=\s*\{([\s\S]*?)\n\}/.exec(readText(DIRS.conf));
  if (!m) return [];
  return [...new Set(Object.values(pyLiteral('{' + m[1] + '}')))];
}

/** 收集所有 geo 定义: identifier -> geometry */
function collectGeometries() {
  const out = new Map();
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { walk(p); continue; }
      if (!e.name.endsWith('.json')) continue;
      let doc;
      try { doc = JSON.parse(readText(p)); } catch (err) { continue; }
      for (const g of doc['minecraft:geometry'] || []) {
        const id = g.description && g.description.identifier;
        if (id && !out.has(id)) out.set(id, g);
      }
    }
  };
  walk(DIRS.models);
  return out;
}

/** 枪身(排除手臂/袖子)的包围盒: cube 和 poly_mesh 都算, inflate 也算 */
function gunBounds(geo) {
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  const put = (x, y, z) => {
    lo[0] = Math.min(lo[0], x); hi[0] = Math.max(hi[0], x);
    lo[1] = Math.min(lo[1], y); hi[1] = Math.max(hi[1], y);
    lo[2] = Math.min(lo[2], z); hi[2] = Math.max(hi[2], z);
  };
  for (const bone of geo.bones || []) {
    const name = bone.name || '';
    if (/arm|sleeve/i.test(name)) continue;
    for (const cube of bone.cubes || []) {
      const inf = cube.inflate || 0;
      const lo = [0, 1, 2].map((i) => cube.origin[i] - inf);
      const hi = [0, 1, 2].map((i) => cube.origin[i] + cube.size[i] + inf);
      for (const x of [lo[0], hi[0]]) {
        for (const y of [lo[1], hi[1]]) {
          for (const z of [lo[2], hi[2]]) put(x, y, z);
        }
      }
    }
    const pm = bone.poly_mesh;
    if (pm && Array.isArray(pm.positions)) {
      const raw = pm.positions;
      if (Array.isArray(raw[0])) {
        for (const v of raw) put(v[0], v[1], v[2]);
      } else {
        for (let i = 0; i + 2 < raw.length; i += 3) put(raw[i], raw[i + 1], raw[i + 2]);
      }
    }
  }
  if (!isFinite(lo[0])) return null;
  return { xmin: lo[0], ymin: lo[1], zmin: lo[2], xmax: hi[0], ymax: hi[1], zmax: hi[2] };
}

/** 按关键字找出需要隐藏的骨骼名 (装填道具等) */
function hiddenBones(geo) {
  return (geo.bones || [])
    .map((b) => b.name || '')
    .filter((name) => HIDE_BONE_KEYWORDS.some((k) => name.toLowerCase().includes(k)));
}

/**
 * 算摆位: 动画里给根骨骼 fpsroot 的 position / rotation
 * 引擎里骨骼变换: v' = pivot + scale * R(v - pivot) + position
 * 反解出让"模型底面贴地、水平居中"的 position
 */
function placement(bounds, pivot) {
  const [px, py, pz] = pivot;
  const maxDim = Math.max(bounds.xmax - bounds.xmin, bounds.ymax - bounds.ymin, bounds.zmax - bounds.zmin);
  const scale = SCALE === 'auto' ? (TARGET_LENGTH * 16) / maxDim : SCALE;
  const rotZ = LAY_FLAT ? 90 : 0;
  const rad = rotZ * Math.PI / 180;
  const c = Math.cos(rad), s = Math.sin(rad);
  const lo = [Infinity, Infinity, Infinity];
  const hi = [-Infinity, -Infinity, -Infinity];
  for (const x of [bounds.xmin, bounds.xmax]) {
    for (const y of [bounds.ymin, bounds.ymax]) {
      for (const z of [bounds.zmin, bounds.zmax]) {
        const dx = x - px, dy = y - py, dz = z - pz;
        const tx = px + scale * (dx * c - dy * s);
        const ty = py + scale * (dx * s + dy * c);
        const tz = pz + scale * dz;
        lo[0] = Math.min(lo[0], tx); hi[0] = Math.max(hi[0], tx);
        lo[1] = Math.min(lo[1], ty); hi[1] = Math.max(hi[1], ty);
        lo[2] = Math.min(lo[2], tz); hi[2] = Math.max(hi[2], tz);
      }
    }
  }
  const round = (v) => Math.round(v * 1000) / 1000;
  return {
    position: [round(-(lo[0] + hi[0]) / 2), round(-lo[1] + LIFT), round(-(lo[2] + hi[2]) / 2)],
    rotation: [0, 0, rotZ],
    scale: round(scale),
    size: [round(hi[0] - lo[0]), round(hi[1] - lo[1]), round(hi[2] - lo[2])],
  };
}

// ---------------------------------------------------------------- builders

function bpEntity(weapon) {
  return {
    format_version: '1.21.50',
    'minecraft:entity': {
      description: {
        identifier: ENTITY_PREFIX + weapon,
        is_spawnable: false,
        is_summonable: true,
      },
      components: {
        'minecraft:type_family': { family: [FAMILY] },
        'minecraft:collision_box': { width: 0.6, height: 0.35 },
        'minecraft:physics': {},
        'minecraft:pushable': { is_pushable: false, is_pushable_by_piston: false },
        'minecraft:health': { value: 1, max: 1 },
        'minecraft:fire_immune': true,
        'minecraft:damage_sensor': { triggers: [{ cause: 'all', deals_damage: false }] },
      },
    },
  };
}

function rpEntity(weapon, res) {
  const textures = { weapon: res.texture };
  if (res.metalTexture) textures.metal = res.metalTexture;
  // 用武器自己的渲染控制器: first_person 列表里去掉手臂那个
  const fp = (res.render && res.render.first_person) || [];
  const controllers = fp.filter((c) => !/first_person\.arm$/.test(c));
  return {
    format_version: '1.12.0',
    'minecraft:client_entity': {
      description: {
        identifier: ENTITY_PREFIX + weapon,
        materials: Object.assign({}, res.materials || {}),
        textures,
        geometry: { default: res.model },
        animations: { place: 'animation.dropped_weapon.' + weapon },
        scripts: { animate: ['place'] },
        render_controllers: controllers.length ? controllers : [FALLBACK_CONTROLLER],
      },
    },
  };
}

function rpAnimation(weapon, place, hide) {
  const root = { position: place.position, rotation: place.rotation };
  if (place.scale !== 1) root.scale = place.scale;
  const bones = { fpsroot: root };
  // 装填道具: scale 0 藏掉 (和武器自带的 gunsmith 动画一个做法, 子骨骼会跟着一起塌掉)
  for (const name of hide) bones[name] = { scale: 0 };
  const anim = {};
  anim['animation.dropped_weapon.' + weapon] = { loop: true, bones };
  return { format_version: '1.8.0', animations: anim };
}

const dump = (obj) => JSON.stringify(obj, null, 4) + '\n';

// ---------------------------------------------------------------- main

function parseArgs(argv) {
  const o = { weapons: [], all: false, dry: false, check: false, quiet: false };
  for (const a of argv) {
    if (a === '--all') o.all = true;
    else if (a === '--dry') o.dry = true;
    else if (a === '--check') o.check = true;
    else if (a === '--quiet') o.quiet = true;
    else if (a === '-h' || a === '--help') o.help = true;
    else if (a.startsWith('-')) throw new Error('未知选项: ' + a);
    else o.weapons.push(a.replace(/\.(geo\.)?json$/, ''));
  }
  return o;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) { console.log('用法: node scripts/gen-dropped-weapon.mjs [weapon...] [--all] [--dry] [--check]'); return 0; }

  let weapons = opts.weapons.slice();
  if (opts.all) {
    weapons = weapons.concat(fs.readdirSync(DIRS.render)
      .filter((f) => f.endsWith('.py') && !f.startsWith('__'))
      .map((f) => f.slice(0, -3)));
  } else if (!weapons.length) {
    weapons = readGunWeapons();
  }
  weapons = [...new Set(weapons)];
  if (!weapons.length) throw new Error('没有要处理的枪 (检查 conf.py 的 GUN_ITEM_NAMES)');

  const geos = collectGeometries();
  let stale = 0;
  let failed = 0;
  const files = [];

  for (const w of weapons) {
    const res = readRenderResource(w);
    if (!res || !res.model || !res.texture) { console.error(w + '  [错误] 缺少 renderResources/' + w + '.py 或 model/texture'); failed++; continue; }
    const geo = geos.get(res.model);
    if (!geo) { console.error(w + '  [错误] 找不到 geometry ' + res.model); failed++; continue; }
    const bounds = gunBounds(geo);
    if (!bounds) { console.error(w + '  [错误] ' + res.model + ' 里没有可用的枪身几何'); failed++; continue; }
    const rootBone = (geo.bones || []).find((b) => b.name === 'fpsroot') || (geo.bones || [])[0];
    const pivot = (rootBone && rootBone.pivot) || [0, 0, 0];
    const place = placement(bounds, pivot);
    const hide = hiddenBones(geo);

    files.push({ file: path.join(DIRS.bpEntity, w + '.json'), text: dump(bpEntity(w)), what: 'BP 实体', weapon: w });
    files.push({ file: path.join(DIRS.rpEntity, w + '.json'), text: dump(rpEntity(w, res)), what: 'RP 客户端实体', weapon: w });
    files.push({ file: path.join(DIRS.rpAnim, w + '.animation.json'), text: dump(rpAnimation(w, place, hide)), what: '摆位动画', weapon: w });

    if (!opts.quiet) {
      console.log(w);
      console.log('  geometry : ' + res.model);
      console.log('  texture  : ' + res.texture);
      console.log('  枪身包围盒: x[%s, %s] y[%s, %s] z[%s, %s]', bounds.xmin.toFixed(1), bounds.xmax.toFixed(1), bounds.ymin.toFixed(1), bounds.ymax.toFixed(1), bounds.zmin.toFixed(1), bounds.zmax.toFixed(1));
      console.log('  摆位     : position=%s rotation=%s scale=%s  (落地后尺寸 %s)',
        JSON.stringify(place.position), JSON.stringify(place.rotation), place.scale, JSON.stringify(place.size));
      console.log('  隐藏骨骼 : %s', hide.length ? hide.join(', ') : '(无)');
      console.log('  渲染控制器: %s', rpEntity(w, res)['minecraft:client_entity'].description.render_controllers.join(', '));
      console.log('  实体     : ' + ENTITY_PREFIX + w);
    }
  }

  for (const f of files) {
    const old = fs.existsSync(f.file) ? readText(f.file) : null;
    if (old === f.text) continue;
    stale++;
    if (!opts.quiet) console.log((f.weapon ? '  ' + f.weapon + '  ' : '') + (old === null ? '新建 ' : '更新 ') + path.relative(ROOT, f.file).split(path.sep).join('/'));
    if (!opts.dry && !opts.check) {
      fs.mkdirSync(path.dirname(f.file), { recursive: true });
      fs.writeFileSync(f.file, f.text);
    }
  }

  const written = opts.dry || opts.check ? 0 : stale;
  console.log('');
  console.log('共 ' + weapons.length + ' 把枪: 需要写入 ' + stale + ' 个文件, 已写入 ' + written + (failed ? ', 失败 ' + failed : ''));
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
