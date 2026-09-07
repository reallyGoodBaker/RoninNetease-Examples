import * as fs from 'fs';
import * as zlib from 'zlib';

function readPng(path: string) {
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
  const channels = { 0:1, 2:3, 4:2, 6:4 }[colorType];
  const raw = zlib.inflateSync(idat);
  const stride = width * channels;
  const rows: Buffer[] = [];
  let prev = Buffer.alloc(stride);
  let p = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[p++];
    const line = Buffer.from(raw.subarray(p, p + stride)); p += stride;
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
        const p = left + up - ul;
        const pa = Math.abs(p - left), pb = Math.abs(p - up), pc = Math.abs(p - ul);
        const pr = pa <= pb && pa <= pc ? left : pb <= pc ? up : ul;
        line[i] = (line[i] + pr) & 0xff;
      }
    }
    rows.push(line);
    prev = line;
  }
  return { width, height, channels, rows };
}

function chunk(type: string, data: Buffer) {
  const c = Buffer.concat([Buffer.from(type), data]);
  const out = Buffer.alloc(12 + data.length);
  out.writeUInt32BE(data.length, 0);
  c.copy(out, 4);
  out.writeUInt32BE(zlib.crc32(c) >>> 0, 8 + data.length);
  return out;
}

function writePng(path: string, width: number, height: number, pixels: number[][]) {
  const rows: Buffer[] = [];
  for (let y = 0; y < height; y++) {
    const row = Buffer.alloc(1 + width * 4);
    row[0] = 0;
    for (let x = 0; x < width; x++) {
      const [r,g,b,a] = pixels[y][x];
      row.writeUInt8(r, 1 + x*4);
      row.writeUInt8(g, 2 + x*4);
      row.writeUInt8(b, 3 + x*4);
      row.writeUInt8(a, 4 + x*4);
    }
    rows.push(row);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 6;
  const png = Buffer.concat([
    Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(Buffer.concat(rows), { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
  fs.writeFileSync(path, png);
}

const src = 'rp/textures/entity/weapons/bolt.png';
const { width, height, channels, rows } = readPng(src);

interface P { r:number; g:number; b:number; a:number }

function pixel(x:number, y:number): P {
  const off = x * channels;
  return {
    r: rows[y][off], g: rows[y][off+1], b: rows[y][off+2],
    a: channels === 4 ? rows[y][off+3] : 255,
  };
}

function makeMask(pred: (p:P)=>boolean) {
  const pixels: number[][][] = [];
  for (let y = 0; y < height; y++) {
    const row: number[][] = [];
    for (let x = 0; x < width; x++) {
      const p = pixel(x,y);
      const val = pred(p) ? 255 : 0;
      row.push([255,255,255,val]);
    }
    pixels.push(row);
  }
  return pixels;
}

const warm = (p:P) => p.a > 64 && ((p.r > 60 && p.r > p.b * 1.2 && p.r >= p.g * 0.75) || (p.r > 120 && p.g > 60 && p.b < 100));
const metal = (p:P) => p.a > 64 && !warm(p);
const full = (p:P) => p.a > 64;
const balance = (p:P) => p.a > 64 && !(p.r < 40 && p.g < 40 && p.b < 40);

const masks: Record<string, (p:P)=>boolean> = {
  'bolt_tint_mask_wood.png': warm,
  'bolt_tint_mask_metal.png': metal,
  'bolt_tint_mask_full.png': full,
  'bolt_tint_mask_balance.png': balance,
};

for (const [name, pred] of Object.entries(masks)) {
  const out = `rp/textures/entity/weapons/${name}`;
  writePng(out, width, height, makeMask(pred));
  console.log('generated', out);
}

fs.copyFileSync('rp/textures/entity/weapons/bolt_tint_mask_balance.png', 'rp/textures/entity/weapons/bolt_tint_mask.png');
console.log('active mask -> bolt_tint_mask.png');
