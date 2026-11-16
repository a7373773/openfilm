
// CLIP zero-shot tagger for extracted frames.
// - model loaded from local mirror cache (no network at runtime)
// - JPEG decoded with jpeg-js + custom CLIP preprocessing (sharp intentionally unused)
// - prompt ensembling: several prompt embeddings averaged per class
// - one ONNX forward per image batch (text embeds are precomputed once)
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

const MODEL_DIR = path.join(CACHE, 'Xenova', 'clip-vit-base-patch32');
const MODEL_ONNX = path.join(MODEL_DIR, 'onnx', 'model_quantized.onnx');
const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD = [0.26862954, 0.26130258, 0.27577711];
const LOGIT_SCALE = 100.0;

// ---------------------------------------------------------------- prompt sets
const CLASSES = {
  landscape: [
    'a beautiful scenic landscape photo of nature, mountains, sky, water',
    'a clear photo of a scenic outdoor landscape with mountains and sky',
    'a wide open view of nature, trees, fields or a lake in daylight',
    'a travel photo of beautiful natural scenery under the open sky',
    'a photo of the sky and clouds above a landscape',
  ],
  hand: [
    'a photo with the camera lens covered by a hand or fingers',
    'a close-up of a hand or fingers blocking the camera lens',
    'an accidental photo of a palm, skin or fingers covering the picture',
  ],
  fabric: [
    'a close-up photo of fabric, clothing or a bag blocking the view',
    'a photo of a jacket, sleeve or bag right in front of the lens',
    'a photo filled with a flat cloth or fabric surface',
  ],
  blurry: [
    'a blurry, dark or unreadable photo where nothing is visible',
    'a photo that is completely out of focus with no recognizable content',
    'a very dark photo where the picture is nearly black',
    'a photo of a plain featureless surface with no detail',
  ],
  ground: [
    'a photo of the ground, floor or wall very close to the camera',
    'the camera is pointed straight down at the ground with no sky and no horizon',
    'a photo filled entirely by dirt, asphalt or concrete with no sky visible',
  ],
};
const SCENES = {
  mountain: ['a photo of snow covered mountains', 'a photo of a mountain range in the distance'],
  water: ['a photo of a wide lake or sea', 'a photo of water, a lake, a river or the ocean'],
  forest: ['a photo of a forest or grass field', 'a photo of green trees and grass'],
  sunset: ['a photo of a sunrise or sunset sky', 'a golden sunset over the horizon'],
  road: ['a photo of a road or highway', 'a road stretching into the distance with landscape and sky around it'],
  city: ['a photo of city buildings', 'a photo of a city skyline with buildings'],
  snow: ['a photo of snow', 'a snowy winter landscape'],
  beach: ['a photo of a sandy beach', 'a photo of a beach with sand and sea'],
  night: ['a photo of the night sky with stars', 'a photo of the night sky'],
};

const CLASS_NAMES = Object.keys(CLASSES);
const SCENE_NAMES = Object.keys(SCENES);
const ALL_PROMPTS = [];
const PROMPT_CLASS = [];
const PROMPT_SCENE = [];
CLASS_NAMES.forEach(n => CLASSES[n].forEach(p => { ALL_PROMPTS.push(p); PROMPT_CLASS.push(n); }));
SCENE_NAMES.forEach(n => SCENES[n].forEach(p => { ALL_PROMPTS.push(p); PROMPT_SCENE.push(n); }));

// ---------------------------------------------------------------- image utils
function decodeAndPrep(file) {
  const img = jpeg.decode(fs.readFileSync(file), { useTArray: true, formatAsRGBA: true });
  const { width: W, height: H, data } = img;
  const scale = 224 / Math.min(W, H);
  const nw = Math.max(224, Math.round(W * scale)), nh = Math.max(224, Math.round(H * scale));
  // bilinear resize to (nw, nh), RGB float 0..1
  const rgb = new Float32Array(nw * nh * 3);
  for (let y = 0; y < nh; y++) {
    let sy = ((y + 0.5) * H / nh) - 0.5; if (sy < 0) sy = 0;
    const y0 = Math.min(H - 1, Math.floor(sy)), y1 = Math.min(H - 1, y0 + 1), fy = sy - y0;
    for (let x = 0; x < nw; x++) {
      let sx = ((x + 0.5) * W / nw) - 0.5; if (sx < 0) sx = 0;
      const x0 = Math.min(W - 1, Math.floor(sx)), x1 = Math.min(W - 1, x0 + 1), fx = sx - x0;
      const i00 = (y0 * W + x0) * 4, i01 = (y0 * W + x1) * 4, i10 = (y1 * W + x0) * 4, i11 = (y1 * W + x1) * 4;
      const o = (y * nw + x) * 3;
      for (let c = 0; c < 3; c++)
        rgb[o + c] = ((data[i00+c]*(1-fx)+data[i01+c]*fx)*(1-fy) + (data[i10+c]*(1-fx)+data[i11+c]*fx)*fy) / 255;
    }
  }
  const left = Math.floor((nw - 224) / 2), top = Math.floor((nh - 224) / 2);
  const t = new Float32Array(3 * 224 * 224);
  for (let c = 0; c < 3; c++)
    for (let y = 0; y < 224; y++)
      for (let x = 0; x < 224; x++)
        t[c*224*224 + y*224 + x] = (rgb[((y+top)*nw + (x+left))*3 + c] - MEAN[c]) / STD[c];
  return t;
}

const norm = (v) => { let s = 0; for (let i = 0; i < v.length; i++) s += v[i]*v[i]; s = Math.sqrt(s) || 1; const o = new Float32Array(v.length); for (let i = 0; i < v.length; i++) o[i] = v[i]/s; return o; };
const softmax = (arr) => { const m = Math.max(...arr); const e = arr.map(v => Math.exp(v - m)); const s = e.reduce((a, b) => a + b, 0); return e.map(v => v / s); };

// ---------------------------------------------------------------- main
const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i+1] : d; };
const OUT_FILE = getArg('--out', path.join(VISION, 'tags.json'));
const SAMPLE = parseInt(getArg('--sample', '0'), 10);
const BATCH = parseInt(getArg('--batch', '8'), 10);
const LIMIT_PER_DIR = parseInt(getArg('--limit', '0'), 10);
const RESUME = args.includes('--resume');

const tokenizer = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
const tf = await tokenizer(ALL_PROMPTS, { padding: true, truncation: true });
const NP = ALL_PROMPTS.length;
const session = await ort.InferenceSession.create(MODEL_ONNX);
console.log('[init] prompts=' + NP + ' classes=' + CLASS_NAMES.length + ' scenes=' + SCENE_NAMES.length);

function classTextEmbeddings() {
  // placeholder: computed inside run() from text_embeds output on the first batch
  return null;
}

// precompute text embeddings once with a zero image
const zeroImg = new ort.Tensor('float32', new Float32Array(3*224*224), [1,3,224,224]);
const idsT = new ort.Tensor('int64', tf.input_ids.data, [NP, tf.input_ids.dims[1]]);
const maskT = new ort.Tensor('int64', tf.attention_mask.data, [NP, tf.input_ids.dims[1]]);
const pre = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: zeroImg });
const pe = pre.text_embeds; // [NP, 512]
const D = pe.dims[1];
const classVec = {}, sceneVec = {};
for (const n of CLASS_NAMES) {
  const acc = new Float32Array(D);
  let k = 0;
  ALL_PROMPTS.forEach((p, i) => { if (PROMPT_CLASS[i] === n) { k++; for (let d = 0; d < D; d++) acc[d] += pe.data[i*D+d]; } });
  classVec[n] = norm(acc);
}
for (const n of SCENE_NAMES) {
  const acc = new Float32Array(D);
  let k = 0;
  ALL_PROMPTS.forEach((p, i) => { if (PROMPT_SCENE[i] === n) { k++; for (let d = 0; d < D; d++) acc[d] += pe.data[i*D+d]; } });
  sceneVec[n] = norm(acc);
}
console.log('[init] class text embeddings built');

const cosTo = (img, vec) => { let s = 0; for (let i = 0; i < D; i++) s += img[i]*vec[i]; return s; };

// ---- collect frame list
const dirs = fs.readdirSync(FRAMES).filter(d => fs.statSync(path.join(FRAMES, d)).isDirectory()).sort();
let files = [];
for (const d of dirs) {
  let fs2 = fs.readdirSync(path.join(FRAMES, d)).filter(f => f.endsWith('.jpg')).sort();
  if (LIMIT_PER_DIR > 0) fs2 = fs2.slice(0, LIMIT_PER_DIR);
  for (const f of fs2) files.push(path.join(FRAMES, d, f));
}
if (SAMPLE > 0 && SAMPLE < files.length) {
  const stride = files.length / SAMPLE; const s2 = [];
  for (let i = 0; i < SAMPLE; i++) s2.push(files[Math.floor(i * stride)]);
  files = s2;
}

// resume support: skip frames already present in ndjson sidecar
const NDJSON = OUT_FILE + '.ndjson';
const done = new Set();
if (RESUME && fs.existsSync(NDJSON)) {
  for (const line of fs.readFileSync(NDJSON, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    try { const o = JSON.parse(line); done.add(o.file + '#' + o.t); } catch (e) {}
  }
  console.log('[resume] already done:', done.size);
}
files = files.filter(f => {
  const rel = path.relative(FRAMES, f).split(path.sep)[0];
  const t = parseInt(path.basename(f, '.jpg').slice(4), 10);
  return !done.has(rel + '#' + t);
});

console.log('[run] frames to process:', files.length, 'batch', BATCH);
const started = Date.now();
const results = {}; // rel -> map t -> rec
let processed = 0;
const nd = fs.createWriteStream(NDJSON, { flags: 'a' });

for (let i = 0; i < files.length; i += BATCH) {
  const chunk = files.slice(i, i + BATCH);
  const pv = new Float32Array(chunk.length * 3 * 224 * 224);
  for (let j = 0; j < chunk.length; j++) {
    const t = decodeAndPrep(chunk[j]);
    pv.set(t, j * 3 * 224 * 224);
  }
  const res = await session.run({
    input_ids: idsT,
    attention_mask: maskT,
    pixel_values: new ort.Tensor('float32', pv, [chunk.length, 3, 224, 224]),
  });
  const ie = res.image_embeds.data; // [B,512]
  for (let j = 0; j < chunk.length; j++) {
    const img = ie.subarray(j*D, (j+1)*D);
    const cl = CLASS_NAMES.map(n => cosTo(img, classVec[n]) * LOGIT_SCALE);
    const sl = SCENE_NAMES.map(n => cosTo(img, sceneVec[n]) * LOGIT_SCALE);
    const cp = softmax(cl), sp = softmax(sl);
    const rec = { p_landscape: +cp[CLASS_NAMES.indexOf('landscape')].toFixed(4) };
    const hand = cp[CLASS_NAMES.indexOf('hand')], fab = cp[CLASS_NAMES.indexOf('fabric')], blur = cp[CLASS_NAMES.indexOf('blurry')];
    rec.p_hand = +hand.toFixed(4); rec.p_fabric = +fab.toFixed(4); rec.p_blurry = +blur.toFixed(4);
    rec.p_closeup = +cp[CLASS_NAMES.indexOf('ground')].toFixed(4);
    rec.p_blocked = +Math.max(hand, fab, blur).toFixed(4);
    let bi = 0; for (let k = 1; k < sp.length; k++) if (sp[k] > sp[bi]) bi = k;
    rec.scene = SCENE_NAMES[bi]; rec.scene_p = +sp[bi].toFixed(4);
    const sl2 = [...sl].sort((a, b) => b - a);
    rec.margin = +(sl2[0] - sl2[1]).toFixed(2); // scene logit margin
    const cl2 = [...cl].sort((a, b) => b - a);
    rec.margin_cls = +(cl2[0] - cl2[1]).toFixed(2);
    const rel = path.relative(FRAMES, chunk[j]).split(path.sep).slice(0, 1)[0] + '.mp4';
    const t = parseInt(path.basename(chunk[j], '.jpg').slice(4), 10);
    (results[rel] = results[rel] || {})[t] = rec;
    nd.write(JSON.stringify({ file: rel, t, ...rec }) + '\n');
    processed++;
  }
  if (i % (BATCH * 20) === 0 || i + BATCH >= files.length) {
    const el = (Date.now() - started) / 1000;
    const rate = processed / el;
    console.log('[prog] ' + processed + '/' + files.length + '  ' + rate.toFixed(1) + ' f/s  eta ' + Math.round((files.length - processed) / rate) + 's');
    // incremental snapshot of tags.json
    const snap = {};
    for (const f of Object.keys(results).sort()) {
      snap[f] = Object.keys(results[f]).map(Number).sort((a, b) => a - b).map(t => ({ t, ...results[f][t] }));
    }
    fs.writeFileSync(OUT_FILE, JSON.stringify(snap, null, 0));
  }
}
nd.end();
const snap = {};
for (const f of Object.keys(results).sort()) {
  snap[f] = Object.keys(results[f]).map(Number).sort((a, b) => a - b).map(t => ({ t, ...results[f][t] }));
}
fs.writeFileSync(OUT_FILE, JSON.stringify(snap, null, 0));
console.log('[done] ' + processed + ' frames in ' + ((Date.now()-started)/1000).toFixed(1) + 's -> ' + OUT_FILE);
