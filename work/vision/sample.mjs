
import fs from 'node:fs';
import path from 'node:path';
import jpeg from 'jpeg-js';
import { env, CLIPModel, AutoTokenizer, Tensor } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const FRAMES = path.join(ROOT, 'work', 'analysis', 'frames');
env.allowRemoteModels = false; env.allowLocalModels = true;
env.localModelPath = path.join(ROOT, 'work', 'vision', 'cache');
const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD = [0.26862954, 0.26130258, 0.27577711];

// resize to nw x nh bilinear, return float RGB 0..1 planar-free (interleaved)
function resizeRGB(img, nw, nh) {
  const { width: W, height: H, data } = img;
  const out = new Float32Array(nw * nh * 3);
  for (let y = 0; y < nh; y++) {
    let sy = ((y + 0.5) * H / nh) - 0.5; if (sy < 0) sy = 0;
    const y0 = Math.min(H - 1, Math.floor(sy)), y1 = Math.min(H - 1, y0 + 1), fy = sy - y0;
    for (let x = 0; x < nw; x++) {
      let sx = ((x + 0.5) * W / nw) - 0.5; if (sx < 0) sx = 0;
      const x0 = Math.min(W - 1, Math.floor(sx)), x1 = Math.min(W - 1, x0 + 1), fx = sx - x0;
      const i00 = (y0*W+x0)*4, i01 = (y0*W+x1)*4, i10 = (y1*W+x0)*4, i11 = (y1*W+x1)*4;
      const o = (y*nw+x)*3;
      for (let c = 0; c < 3; c++) out[o+c] = ((data[i00+c]*(1-fx)+data[i01+c]*fx)*(1-fy) + (data[i10+c]*(1-fx)+data[i11+c]*fx)*fy) / 255;
    }
  }
  return out;
}

function stats(rgb, w, h) {
  let sum = 0, sum2 = 0, sat = 0, minv = 1, maxv = 0;
  const gray = new Float32Array(w*h);
  for (let i = 0, p = 0; i < w*h; i++, p += 3) {
    const r = rgb[p], g = rgb[p+1], b = rgb[p+2];
    const y = 0.299*r + 0.587*g + 0.114*b;
    gray[i] = y; sum += y; sum2 += y*y;
    const mx = Math.max(r,g,b), mn = Math.min(r,g,b);
    sat += (mx > 1e-6 ? (mx-mn)/mx : 0);
    if (y < minv) minv = y; if (y > maxv) maxv = y;
  }
  const n = w*h;
  const mean = sum/n, std = Math.sqrt(Math.max(0, sum2/n - mean*mean));
  // laplacian variance (sharpness)
  let lsum = 0, lsum2 = 0, ln = 0;
  for (let y = 1; y < h-1; y++) for (let x = 1; x < w-1; x++) {
    const i = y*w+x;
    const v = -4*gray[i] + gray[i-1] + gray[i+1] + gray[i-w] + gray[i+w];
    lsum += v; lsum2 += v*v; ln++;
  }
  const lmean = lsum/ln;
  const lapVar = lsum2/ln - lmean*lmean;
  return { mean, std, sat: sat/n, lapVar, contrast: maxv-minv };
}

function prep(rgb, w, h) {
  const scale = 224 / Math.min(w, h);
  const nw = Math.max(224, Math.round(w*scale)), nh = Math.max(224, Math.round(h*scale));
  const rs = resizeRGB({ width: w, height: h, data: rgb.__rgba }, nw, nh);
  const left = Math.floor((nw-224)/2), top = Math.floor((nh-224)/2);
  const t = new Float32Array(3*224*224);
  for (let c = 0; c < 3; c++) for (let y = 0; y < 224; y++) for (let x = 0; x < 224; x++)
    t[c*224*224 + y*224 + x] = (rs[((y+top)*nw + (x+left))*3 + c] - MEAN[c]) / STD[c];
  return t;
}

const BLOCKED = [
  'a beautiful scenic landscape photo of nature, mountains, sky, water',
  'a photo with the camera lens covered by a hand or fingers',
  'a close-up photo of fabric, clothing or a bag blocking the view',
  'a blurry, dark or unreadable photo where nothing is visible',
  'a photo of the ground, floor or wall very close to the camera',
];
const SCENE = [
  'a photo of snow covered mountains','a photo of a wide lake or sea','a photo of a forest or grass field',
  'a photo of a sunrise or sunset sky','a photo of a road or highway','a photo of city buildings',
  'a photo of snow','a photo of a sandy beach','a photo of the night sky with stars',
];
const LABELS = [...BLOCKED, ...SCENE];
const softmax = (arr) => { const m = Math.max(...arr); const e = arr.map(v => Math.exp(v-m)); const s = e.reduce((a,b)=>a+b,0); return e.map(v=>v/s); };

const model = await CLIPModel.from_pretrained('Xenova/clip-vit-base-patch32', { quantized: true });
const tokenizer = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
const tf = await tokenizer(LABELS, { padding: true, truncation: true });

// collect sample: every 8th frame from each dir, cap 4 per dir
const dirs = fs.readdirSync(FRAMES).filter(d => fs.statSync(path.join(FRAMES,d)).isDirectory()).sort();
const samples = [];
for (const d of dirs) {
  const files = fs.readdirSync(path.join(FRAMES, d)).filter(f => f.endsWith('.jpg')).sort();
  const step = Math.max(1, Math.floor(files.length / 4));
  for (let i = 0; i < files.length; i += step) samples.push(path.join(FRAMES, d, files[i]));
}
console.log('sample count', samples.length);

const rows = [];
for (const f of samples) {
  const buf = fs.readFileSync(f);
  const img = jpeg.decode(buf, { useTArray: true, formatAsRGBA: true });
  const rgba = img.data;
  // build float rgba array for reuse
  const floatrgba = new Float32Array(rgba.length);
  for (let i = 0; i < rgba.length; i++) floatrgba[i] = rgba[i]/255;
  const st = stats(floatrgba, img.width, img.height);
  const pv = prep({ __rgba: floatrgba }, img.width, img.height);
  const out = await model({ input_ids: tf.input_ids, attention_mask: tf.attention_mask, pixel_values: new Tensor('float32', pv, [1,3,224,224]) });
  const lg = out.logits_per_image.data;
  const pb = softmax(lg.slice(0,5)), ps = softmax(lg.slice(5));
  const pBlocked = Math.max(pb[1],pb[2],pb[3]);
  const best = ps.indexOf(Math.max(...ps));
  rows.push({ f: path.basename(path.dirname(f)) + '/' + path.basename(f, '.jpg'), kb: Math.round(buf.length/1024),
    land: pb[0], hand: pb[1], fab: pb[2], blur: pb[3], close: pb[4], pBlocked, scene: SCENE[best], sceneP: ps[best],
    ...st });
}

console.log('\nfile'.padEnd(24) + 'kb'.padStart(4) + ' land  hand  fab  blur close | pBlk  | mean  std   sat  lapVar contrast | scene (p)');
for (const r of rows) {
  console.log(r.f.padEnd(24) + String(r.kb).padStart(4) +
    ' ' + [r.land,r.hand,r.fab,r.blur,r.close].map(v=>v.toFixed(2)).join(' ') +
    ' | ' + r.pBlocked.toFixed(2) +
    ' | ' + [r.mean,r.std,r.sat,r.lapVar,r.contrast].map(v=>v.toFixed(3)).join(' ') +
    ' | ' + r.scene.replace('a photo of ','') + ' (' + r.sceneP.toFixed(2) + ')');
}
