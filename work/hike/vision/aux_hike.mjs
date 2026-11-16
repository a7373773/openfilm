
// Independent second-opinion CLIP pass with different wording, to test label stability.
import fs from 'node:fs';
import path from 'node:path';
import jpeg from 'jpeg-js';
import ort from 'onnxruntime-node';
import { env, AutoTokenizer } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const CACHE = path.join(ROOT, 'work', 'vision', 'cache');
env.allowRemoteModels = false; env.allowLocalModels = true; env.localModelPath = CACHE;
const MODEL_ONNX = path.join(CACHE, 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD = [0.26862954, 0.26130258, 0.27577711];
const LOGIT_SCALE = 100.0;

const GROUPS = {
  human: {
    yes: ['a human being is somewhere in this photo, hiking outdoors',
          'a person out walking in nature, visible in the shot'],
    no:  ['there is no human being anywhere in this photo',
          'empty nature without any people at all'],
  },
  groundview: {
    down: ['this photo was taken looking straight down at the path at the walker feet',
           'the ground and rocks fill the frame from above'],
    level: ['this photo looks straight ahead at the horizon',
            'a level shot of the surroundings at eye height'],
  },
  widevista: {
    wide: ['a wide open scenic vista stretching to distant mountains',
           'a broad view over a valley from up high'],
    narrow: ['a crowded close view with objects very near the camera',
             'a photo where the view is blocked or very close'],
  },
  backpack: {
    bag: ['a backpack or a rear of a person filling the picture right in front of the camera',
          'a close view of a hiking backpack moving in front of the lens'],
    nobag: ['a normal photo with a clear open view of the scenery',
            'the scene is visible with nothing large right in front of the camera'],
  },
};
const GROUP_NAMES = Object.keys(GROUPS);
const classes = [];
for (const g of GROUP_NAMES) for (const c of Object.keys(GROUPS[g])) classes.push({ group: g, name: c, prompts: GROUPS[g][c] });

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

const args = process.argv.slice(2);
const getArg = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i+1] : d; };
const FRAMES = getArg('--frames', '');
const OUT = getArg('--out', '');
const BATCH = 12;

const tok = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
const allPrompts = [], promptOf = [];
classes.forEach((c, ci) => c.prompts.forEach(p => { allPrompts.push(p); promptOf.push(ci); }));
const tf = await tok(allPrompts, { padding: true, truncation: true });
const session = await ort.InferenceSession.create(MODEL_ONNX);
const NP = allPrompts.length;
const idsT = new ort.Tensor('int64', tf.input_ids.data, [NP, tf.input_ids.dims[1]]);
const maskT = new ort.Tensor('int64', tf.attention_mask.data, [NP, tf.attention_mask.dims[1]]);
const zero = new ort.Tensor('float32', new Float32Array(3*224*224), [1,3,224,224]);
const pre = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: zero });
const D = pre.text_embeds.dims[1];
const acc = classes.map(() => new Float32Array(D));
allPrompts.forEach((p, i) => { const ci = promptOf[i]; for (let d = 0; d < D; d++) acc[ci][d] += pre.text_embeds.data[i*D+d]; });
const classVec = acc.map(v => norm(v));

const clips = fs.readdirSync(FRAMES).filter(d => fs.statSync(path.join(FRAMES, d)).isDirectory()).sort();
const items = [];
for (const c of clips) for (const f of fs.readdirSync(path.join(FRAMES, c)).filter(x => x.endsWith('.jpg')).sort())
  items.push({ clip: c, file: path.join(FRAMES, c, f), seq: parseInt(f.slice(4, 8), 10) });

const out = {};
const fmt = (v) => +v.toFixed(4);
const t0 = Date.now();
for (let i = 0; i < items.length; i += BATCH) {
  const chunk = items.slice(i, i + BATCH);
  const pv = new Float32Array(chunk.length*3*224*224);
  for (let j = 0; j < chunk.length; j++) pv.set(decodeAndPrep(chunk[j].file), j*3*224*224);
  const res = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: new ort.Tensor('float32', pv, [chunk.length,3,224,224]) });
  const ie = res.image_embeds.data;
  for (let j = 0; j < chunk.length; j++) {
    const img = ie.subarray(j*D, (j+1)*D);
    const logit = classes.map((c, ci) => { let s = 0; for (let k = 0; k < D; k++) s += img[k]*classVec[ci][k]; return s*LOGIT_SCALE; });
    const probs = {};
    for (const g of GROUP_NAMES) {
      const idxs = classes.map((c, ci) => c.group === g ? ci : -1).filter(x => x >= 0);
      const sp = softmax(idxs.map(ci => logit[ci]));
      idxs.forEach((ci, k) => probs[classes[ci].name] = sp[k]);
    }
    const it = chunk[j];
    const rec = { p_human: fmt(probs.yes), p_ground2: fmt(probs.down), p_wide2: fmt(probs.wide), p_bag2: fmt(probs.bag) };
    (out[it.clip] = out[it.clip] || []).push({ seq: it.seq, ...rec });
  }
  if (i % (BATCH*30) === 0) console.log('[prog] ' + i + '/' + items.length);
}
fs.writeFileSync(OUT, JSON.stringify(out));
console.log('[done] ' + items.length + ' frames in ' + ((Date.now()-t0)/1000).toFixed(1) + 's -> ' + OUT);
