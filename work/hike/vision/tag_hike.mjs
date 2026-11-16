
// Hike CLIP tagger v3.
// "view" group (6 mutually-exclusive camera framings) is the primary signal for the
// editor's three questions: back-of-hiker motion shots, ground/feet/backpack waste
// shots, and wide summit vistas for the ending.
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
  presence: {
    one:   ['a photo of a single hiker walking on a mountain trail',
            'a photo with one person in the frame, hiking outdoors',
            'a person hiking through nature, one person visible'],
    multi: ['a photo of a group of hikers walking together on a trail',
            'a photo with several people hiking in the mountains',
            'two or more people walking on a mountain path'],
    none:  ['a photo of an empty mountain landscape with no people anywhere',
            'a photo of nature scenery with nobody in the frame',
            'an unpopulated hiking trail with no person visible'],
  },
  view: {
    back_far:   ['a hiker seen from behind at a distance on the trail, whole body small in the frame',
                 'a person walking away from the camera further down the path, environment visible around them'],
    back_close: ['the back of a hiker very close to the camera, their backpack filling a large part of the frame',
                 'a large backpack or the back of a person right in front of the lens taking up the picture'],
    ahead_path: ['an empty trail ahead with no person in the foreground, the path leading away',
                 'looking down the hiking path with nobody directly in front of the camera'],
    ground_feet:['only the ground, rocks, dirt or the walker own feet fill the frame',
                 'the camera is aimed at the ground and boots just below the lens'],
    vista_wide: ['a wide open panorama of mountains, valleys and sky with no person nearby',
                 'a broad landscape view from a high point with the horizon far away'],
    facing:     ['a person facing towards the camera in the picture',
                 'a hiker looking at the camera, front of the body visible'],
  },
  occlusion: {
    blocked: ['a photo where a hand, fingers, clothing or a backpack is covering the camera lens',
              'something is right in front of the lens, a cloth or a bag blocking the view',
              'the lens is obstructed by a hand or by clothing'],
    clear:   ['a photo of a clear view of the surroundings, nothing blocking the lens',
              'a normal unobstructed shot of the outdoors'],
  },
  quality: {
    sharp: ['a sharp, clean, in-focus photo with clear detail',
            'a crisp photo where everything is well focused'],
    blur:  ['an out-of-focus blurry photo with no clear detail',
            'a motion blurred photo where nothing is sharp'],
    dark:  ['a dark underexposed photo where the image is very dim',
            'a nearly black photo with very low light'],
  },
  landscape: {
    wide:    ['a wide scenic landscape view of mountains, a forest or the open sky',
              'a photo of a broad mountain view extending into the distance',
              'a beautiful nature scene with the landscape filling the frame'],
    subject: ['a close view of a person, a backpack or an object filling most of the frame',
              'a photo dominated by a person in the foreground'],
    unclear: ['an unclear blurry image where nothing can be recognized',
              'a photo of the ground or a random texture with no scenery'],
  },
  scene: {
    trail:    ['a photo of a narrow dirt hiking trail or footpath through the mountains',
               'a mountain trail made of dirt, rocks and roots'],
    forest:   ['a photo of a forest with tall trees and green vegetation',
               'a woodland path surrounded by trees and bushes'],
    mountain: ['a photo of a mountain ridge or peak in the distance',
               'distant mountain layers under the sky'],
    summit:   ['a photo of an open panoramic view from a mountain summit, valleys and sky',
               'a wide vista from the top of a mountain with nothing in the foreground'],
    sky:      ['a photo mostly filled with the sky and clouds',
               'blue sky and clouds taking up most of the picture'],
    water:    ['a photo of a lake, a river or the sea',
               'a body of water in the mountains'],
    other:    ['a photo of something else, an object or an unclear subject',
               'a photo of a person close-up or a texture filling the frame'],
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
const FRAMES = getArg('--frames', path.join(ROOT, 'work', 'hike', 'analysis', 'frames'));
const OUT = getArg('--out', path.join(ROOT, 'work', 'hike', 'vision', 'tags.json'));
const BATCH = parseInt(getArg('--batch', '12'), 10);

const tok = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
const allPrompts = [], promptOf = [];
classes.forEach((c, ci) => c.prompts.forEach(p => { allPrompts.push(p); promptOf.push(ci); }));
const tf = await tok(allPrompts, { padding: true, truncation: true });
const NP = allPrompts.length;
const session = await ort.InferenceSession.create(MODEL_ONNX);
const idsT = new ort.Tensor('int64', tf.input_ids.data, [NP, tf.input_ids.dims[1]]);
const maskT = new ort.Tensor('int64', tf.attention_mask.data, [NP, tf.attention_mask.dims[1]]);
const zero = new ort.Tensor('float32', new Float32Array(3*224*224), [1,3,224,224]);
const pre = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: zero });
const D = pre.text_embeds.dims[1];
const acc = classes.map(() => new Float32Array(D));
allPrompts.forEach((p, i) => { const ci = promptOf[i]; for (let d = 0; d < D; d++) acc[ci][d] += pre.text_embeds.data[i*D+d]; });
const classVec = acc.map(v => norm(v));
console.log('[init] groups=' + GROUP_NAMES.length + ' classes=' + classes.length + ' prompts=' + NP);

const clipDirs = fs.readdirSync(FRAMES).filter(d => fs.statSync(path.join(FRAMES, d)).isDirectory()).sort();
const items = [];
for (const c of clipDirs) for (const f of fs.readdirSync(path.join(FRAMES, c)).filter(x => x.endsWith('.jpg')).sort())
  items.push({ clip: c, file: path.join(FRAMES, c, f), seq: parseInt(f.slice(4, 8), 10) });
console.log('[run] clips=' + clipDirs.length + ' frames=' + items.length);
const t0 = Date.now();
const perClip = {};
const nd = fs.createWriteStream(OUT + '.ndjson');
const fmt = (v) => +v.toFixed(4);

for (let i = 0; i < items.length; i += BATCH) {
  const chunk = items.slice(i, i + BATCH);
  const pv = new Float32Array(chunk.length*3*224*224);
  for (let j = 0; j < chunk.length; j++) pv.set(decodeAndPrep(chunk[j].file), j*3*224*224);
  const res = await session.run({ input_ids: idsT, attention_mask: maskT, pixel_values: new ort.Tensor('float32', pv, [chunk.length, 3, 224, 224]) });
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
    const rec = {
      t: +(((it.seq - 1) * 0.5).toFixed(1)),
      p_person: fmt(probs.one + probs.multi),
      p_people: fmt(probs.multi),
      p_nobody: fmt(probs.none),
      p_back: fmt(probs.back_far + probs.back_close),
      p_back_far: fmt(probs.back_far),
      p_back_close: fmt(probs.back_close),
      p_facing: fmt(probs.facing),
      p_trail_ahead: fmt(probs.ahead_path),
      p_ground: fmt(probs.ground_feet),
      p_closeup: fmt(probs.ground_feet),
      p_wide_vista: fmt(probs.vista_wide),
      p_landscape: fmt(probs.wide),
      p_clear: fmt(probs.sharp),
      p_hand: 0, p_fabric: 0,
      p_blocked: fmt(probs.blocked),
      p_blurry: fmt(probs.blur + probs.dark),
      scene: '', scene_p: 0, view: '',
    };
    const vn = Object.keys(GROUPS.view);
    let vi = 0; for (let k = 1; k < vn.length; k++) if (probs[vn[k]] > probs[vn[vi]]) vi = k;
    rec.view = vn[vi];
    const sn = Object.keys(GROUPS.scene);
    let bi = 0; for (let k = 1; k < sn.length; k++) if (probs[sn[k]] > probs[sn[bi]]) bi = k;
    rec.scene = sn[bi];
    rec.scene_p = fmt(probs[sn[bi]]);
    (perClip[it.clip] = perClip[it.clip] || []).push(rec);
    nd.write(JSON.stringify({ clip: it.clip, ...rec }) + '\n');
  }
  if (i % (BATCH*25) === 0 || i + BATCH >= items.length) {
    const el = (Date.now()-t0)/1000;
    console.log('[prog] ' + (i+chunk.length) + '/' + items.length + '  ' + ((i+chunk.length)/el).toFixed(1) + ' f/s');
  }
}
nd.end();

const allL = [];
for (const c of Object.keys(perClip)) for (const r of perClip[c]) allL.push(r.p_landscape);
const sortedL = [...allL].sort((a, b) => a - b);
function lowerBound(arr, v) { let lo = 0, hi = arr.length; while (lo < hi) { const m = (lo+hi)>>1; if (arr[m] < v) lo = m+1; else hi = m; } return lo; }
const pctRank = (v) => +(lowerBound(sortedL, v) / sortedL.length).toFixed(4);
const tags = {};
for (const c of Object.keys(perClip).sort()) tags[c + '.mp4'] = perClip[c].sort((a, b) => a.t - b.t).map(r => ({ ...r, p_landscape_pct: pctRank(r.p_landscape) }));
fs.writeFileSync(OUT, JSON.stringify(tags));
console.log('[done] ' + items.length + ' frames in ' + ((Date.now()-t0)/1000).toFixed(1) + 's -> ' + OUT);
