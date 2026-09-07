// 基于原版 SMLE 贴图做“去真实化”橙蓝 recolor：
// 保留原图明暗结构（HSL 的 L 尽量保留），只换色相/饱和度，让枪还能看出形状。
// 用法: node tools/gen_bolt_stylized.cjs
const fs = require('fs');
const zlib = require('zlib');

function readPng(path) {
  const data = fs.readFileSync(path);
  let pos = 8;
  let idat = Buffer.alloc(0);
  let width = 0, height = 0, colorType = 0;
  while (pos < data.length) {
    const length = data.readUInt32BE(pos);
    const type = data.toString('ascii', pos + 4, pos + 8);
    const chunk = data.subarray(pos + 8, pos + 8 + length);
    if (type === 'IHDR') {
      width = chunk.readUInt32BE(0);
      height = chunk.readUInt32BE(4);
      colorType = chunk[9];
    } else if (type === 'IDAT') {
      idat = Buffer.concat([idat, chunk]);
    }
    pos += 12 + length;
  }
  const channels = { 0: 1, 2: 3, 4: 2, 6: 4 }[colorType];
  const raw = zlib.inflateSync(idat);
  const stride = width * channels;
  const rows = [];
  let prev = Buffer.alloc(stride);
  let p = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[p++];
    const line = Buffer.from(raw.subarray(p, p + stride));
    p += stride;
    if (filter === 1) {
      for (let i = channels; i < stride; i++) line[i] = (line[i] + line[i - channels]) & 0xff;
    } else if (filter === 2) {
      for (let i = 0; i < stride; i++) line[i] = (line[i] + prev[i]) & 0xff;
    } else if (filter === 3) {
      for (let i = 0; i < stride; i++) {
        const left = i >= channels ? line[i - channels] : 0;
        line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xff;
      }
    } else if (filter === 4) {
      for (let i = 0; i < stride; i++) {
        const left = i >= channels ? line[i - channels] : 0;
        const up = prev[i];
        const ul = i >= channels ? prev[i - channels] : 0;
        const pp = left + up - ul;
        const pa = Math.abs(pp - left);
        const pb = Math.abs(pp - up);
        const pc = Math.abs(pp - ul);
        const pr = pa <= pb && pa <= pc ? left : pb <= pc ? up : ul;
        line[i] = (line[i] + pr) & 0xff;
      }
    }
    rows.push(line);
    prev = line;
  }
  return { width, height, channels, rows };
}

function chunk(type, data) {
  const c = Buffer.concat([Buffer.from(type), data]);
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  c.copy(out, 4);
  out.writeUInt32BE(zlib.crc32(c) >>> 0, 8 + data.length);
  return out;
}

function writePng(path, width, height, pixels) {
  const rows = [];
  for (let y = 0; y < height; y++) {
    const row = Buffer.alloc(1 + width * 4);
    row[0] = 0;
    for (let x = 0; x < width; x++) {
      const [r, g, b, a] = pixels[y][x];
      row.writeUInt8(clamp255(r), 1 + x * 4);
      row.writeUInt8(clamp255(g), 2 + x * 4);
      row.writeUInt8(clamp255(b), 3 + x * 4);
      row.writeUInt8(clamp255(a), 4 + x * 4);
    }
    rows.push(row);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(Buffer.concat(rows), { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
  fs.writeFileSync(path, png);
}

function clamp255(v) { return Math.max(0, Math.min(255, Math.round(v))); }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  const l = (max + min) / 2;
  if (max === min) return [0, 0, l];
  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
  let h;
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / d + 2) / 6;
  else h = ((r - g) / d + 4) / 6;
  return [h, s, l];
}

function hslToRgb(h, s, l) {
  if (s === 0) {
    const v = l * 255;
    return [v, v, v];
  }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  const r = hue2rgb(p, q, h + 1 / 3);
  const g = hue2rgb(p, q, h);
  const b = hue2rgb(p, q, h - 1 / 3);
  return [r * 255, g * 255, b * 255];
}

function hue2rgb(p, q, t) {
  if (t < 0) t += 1;
  if (t > 1) t -= 1;
  if (t < 1 / 6) return p + (q - p) * 6 * t;
  if (t < 1 / 2) return q;
  if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
  return p;
}

function isWarm(r, g, b) {
  return (r > 60 && r > b * 1.2 && r >= g * 0.75) || (r > 120 && g > 60 && b < 100);
}

function stylizePixel(r, g, b, a) {
  if (a <= 64) return [0, 0, 0, 0];
  const [h, s, l] = rgbToHsl(r, g, b);
  if (isWarm(r, g, b)) {
    // 暖色/木托 -> 橙，保留原明度
    const h2 = 30 / 360;
    const s2 = clamp(s * 0.5 + 0.45, 0.5, 0.75);
    const [r2, g2, b2] = hslToRgb(h2, s2, l);
    return [r2, g2, b2, a];
  }
  // 金属 -> 真实感中性灰，保留原图明度
  const h2 = 215 / 360;
  const s2 = 0.0;
  const l2 = l;
  const [r2, g2, b2] = hslToRgb(h2, s2, l2);
  return [r2, g2, b2, a];
}

function recolorFile(src, dst) {
  const { width, height, channels, rows } = readPng(src);
  const pixels = [];
  for (let y = 0; y < height; y++) {
    const row = [];
    for (let x = 0; x < width; x++) {
      const off = x * channels;
      const r = rows[y][off];
      const g = rows[y][off + 1];
      const b = rows[y][off + 2];
      const a = channels === 4 ? rows[y][off + 3] : 255;
      row.push(stylizePixel(r, g, b, a));
    }
    pixels.push(row);
  }
  writePng(dst, width, height, pixels);
  console.log('stylized', src, '->', dst);
}

recolorFile('rp/textures/entity/weapons/bolt.png', 'rp/textures/entity/weapons/bolt.png');
recolorFile('rp/textures/item/weapons/bolt.png', 'rp/textures/item/weapons/bolt.png');
