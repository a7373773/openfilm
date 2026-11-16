
// Auxiliary CLIP pass: separate "real detailed scenery" from "empty/overexposed sky".
import fs from 'node:fs';
import path from 'node:path';
import jpeg from 'jpeg-js';
import ort from 'onnxruntime-node';
import { env, AutoTokenizer } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const VISION = path.join(ROOT, 'work', 'vision');
const FRAMES = path.join(ROOT, 'work', 'analysis', 'frames');
const CACHE = path.join(VISION, 'cache');
env.allowRemoteModels = false; env.allowLocalModels = true; env.localModelPath = CACHE;
const MODEL_ONNX = path.join(CACHE, 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD = [0.26862954, 0.26130258, 0.27577711];
const LOGIT_SCALE = 100.0;

const CLASSES = {
  clear_scenery: [
    'a photo of a scenic landscape with visible mountains, water, trees or terrain',
    'a photo with clear detail of nature: rocks, trees, grass, water or a road',
    'a sharp clear photo of an outdoor scene with visible texture and detail',
  ],
  empty_sky: [
    'a plain empty sky with no landscape or terrain visible',
    'a photo of nothing but bright white overcast sky or haze',
  ],
  washed: [
    'an overexposed washed out image with almost no contrast',
    'a hazy low contrast photo with a flat pale look',
  ],
  obstruction: [
    'a photo with a hand, fingers or clothing in front of the lens',
    'a photo that is mostly an unreadable blur or a dark blob',
  ],
};
const CLASS_NAMES = Object.keys(CLASSES);
const PROMPTS = [], PROMPT_CLASS = [];
CLASS_NAMES.forEach(n => CLASSES[n].forEach(p => { PROMPTS.push(p); PROMPT_CLASS.push(n); }));

function decodeAndPrep(file) {
  const img = jpeg.decode(fs.readFileSync(file), { useTArray: true, formatAsRGBA: true });
  const { width: W, height: H, data } = img;
  const scale = 224 / Math.min(W, H);
  const nw = Math.max(224, Math.round(W * scale)), nh = Math.max(224, Math.round(H * scale));
  const rgb = new Float32Array(nw * nh * 3);
  for (let y = 0; y < nh; y++) {
    let sy = ((y + 0.5) * H / nh) - 0.5; if (sy < 0) sy = 0;
    const y0 = Math.min(H - 1, Math.floor(sy)), y1 = Math.min(H - 1, y0 + 1), fy = sy - y0;
    for (let x = 0; x < nw; x++) {
      let sx = ((x + 0.5) * W / nw) - 0.5; if (sx < 0) sx = 0;
      const x0 = Math.min(W - 1, Math.floor(sx)), x1 = Math.min(W - 1, x0 + 1), fx = sx - x0;
      const i00 = (y0*W+x0)*4, i01 = (y0*W+x1)*4, i10 = (y1*W+x0)*4, i11 = (y1*W+x1)*4;
      const o = (y*nw+x)*3;
      for (let c = 0; c < 3; c++)
        rgb[o+c] = ((data[i00+c]*(1-fx)+data[i01+c]*fx)*(1-fy) + (data[i10+c]*(1-fx)+data[i11+c]*fx)*fy) / 255;
    }
  }
  const left = Math.floor((nw - 224) / 2), top = Math.floor((nh - 224) / 2);
  const t = new Float32Array(3*224*224);
  for (let c = 0; c < 3; c++) for (let y = 0; y < 224; y++) for (let x = 0; x < 224; x++)
    t[c*224*224 + y*224 + x] = (rgb[((y+top)*nw + (x+left))*3 + c] - MEAN[c]) / STD[c];
  return t;
}
const norm = (v) => { let s = 0; for (let i = 0; i < v.length; i++) s += v[i]*v[i]; s = Math.sqrt(s) || 1; const o = new Float32Array(v.length); for (let i = 0; i < v.length; i++) o[i] = v[i]/s; return o; };
const softmax = (arr) => { const m = Math.max(...arr); const e = arr.map(v => Math.exp(v - m)); const s = e.reduce((a, b) => a + b, 0); return e.map(v => v / s); };

const tok = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
const tf = await tok(PROMPTS, { padding: true, truncation: true });
const NP = PROMPTS.length;
const session = await ort.InferenceSession.create(MODEL_ONNX);
const idsT = new ort.Tensor('int64', tf.input_ids.data, [NP, tf.input_ids.dims[1]]);
const maskT = new ort.Tensor('int64', tf.attention_mask.data, [NP, tf.attention_mask.dims[1]]);
const zero = new ort.Tensor('float32', new Float32Array(3*224*224), [1,3,224,224]);
const pre = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: zero });
const D = pre.text_embeds.dims[1];
const vecs = {};
for (const n of CLASS_NAMES) {
  const acc = new Float32Array(D);
  PROMPTS.forEach((p, i) => { if (PROMPT_CLASS[i] === n) for (let d = 0; d < D; d++) acc[d] += pre.text_embeds.data[i*D+d]; });
  vecs[n] = norm(acc);
}

const dirs = fs.readdirSync(FRAMES).filter(d => fs.statSync(path.join(FRAMES, d)).isDirectory()).sort();
const files = [];
for (const d of dirs) for (const f of fs.readdirSync(path.join(FRAMES, d)).filter(f => f.endsWith('.jpg')).sort()) files.push(path.join(FRAMES, d, f));
const BATCH = 16;
const out = {};
const nd = fs.createWriteStream(path.join(VISION, 'aux.json.ndjson'));
const t0 = Date.now();
for (let i = 0; i < files.length; i += BATCH) {
  const chunk = files.slice(i, i + BATCH);
  const pv = new Float32Array(chunk.length*3*224*224);
  for (let j = 0; j < chunk.length; j++) pv.set(decodeAndPrep(chunk[j]), j*3*224*224);
  const res = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: new ort.Tensor('float32', pv, [chunk.length,3,224,224]) });
  const ie = res.image_embeds.data;
  for (let j = 0; j < chunk.length; j++) {
    const img = ie.subarray(j*D, (j+1)*D);
    const cl = CLASS_NAMES.map(n => { let s = 0; for (let k = 0; k < D; k++) s += img[k]*vecs[n][k]; return s*LOGIT_SCALE; });
    const sp = softmax(cl);
    const rec = {}; CLASS_NAMES.forEach((n, k) => rec['p_' + n] = +sp[k].toFixed(4));
    rec.p_blank = +(sp[CLASS_NAMES.indexOf('empty_sky')] + sp[CLASS_NAMES.indexOf('washed')]).toFixed(4);
    const rel = path.relative(FRAMES, chunk[j]).split(path.sep);
    const file = rel[0] + '.mp4';
    const t = parseInt(path.basename(chunk[j], '.jpg').slice(4), 10);
    (out[file] = out[file] || {})[t] = rec;
    nd.write(JSON.stringify({ file, t, ...rec }) + '\n');
  }
  if (i % (BATCH*40) === 0) console.log('[prog] ' + i + '/' + files.length);
}
nd.end();
fs.writeFileSync(path.join(VISION, 'aux.json'), JSON.stringify(out));
console.log('[done] ' + files.length + ' frames in ' + ((Date.now()-t0)/1000).toFixed(1) + 's');
