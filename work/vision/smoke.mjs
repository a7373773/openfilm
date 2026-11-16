
import fs from 'node:fs';
import path from 'node:path';
import jpeg from 'jpeg-js';
import { env, CLIPModel, AutoTokenizer, Tensor } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const CACHE = path.join(ROOT, 'work', 'vision', 'cache');

env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = CACHE;
env.useFSCache = true;

const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD  = [0.26862954, 0.26130258, 0.27577711];

function decodeToPixels(file) {
  const raw = jpeg.decode(fs.readFileSync(file), { useTArray: true, formatAsRGBA: true });
  return raw; // {width,height,data}
}

// bilinear resize RGB -> Float32 planar, keeping float 0..1
function resizeRGB(img, newW, newH) {
  const { width: W, height: H, data } = img;
  const out = new Float32Array(newW * newH * 3);
  for (let y = 0; y < newH; y++) {
    let sy = ((y + 0.5) * H / newH) - 0.5;
    if (sy < 0) sy = 0;
    let y0 = Math.floor(sy), y1 = Math.min(H - 1, y0 + 1), fy = sy - y0;
    if (y0 > H - 1) y0 = H - 1;
    for (let x = 0; x < newW; x++) {
      let sx = ((x + 0.5) * W / newW) - 0.5;
      if (sx < 0) sx = 0;
      let x0 = Math.floor(sx), x1 = Math.min(W - 1, x0 + 1), fx = sx - x0;
      if (x0 > W - 1) x0 = W - 1;
      const i00 = (y0 * W + x0) * 4, i01 = (y0 * W + x1) * 4, i10 = (y1 * W + x0) * 4, i11 = (y1 * W + x1) * 4;
      const o = (y * newW + x) * 3;
      for (let c = 0; c < 3; c++) {
        const v = (data[i00 + c] * (1 - fx) + data[i01 + c] * fx) * (1 - fy)
                + (data[i10 + c] * (1 - fx) + data[i11 + c] * fx) * fy;
        out[o + c] = v / 255;
      }
    }
  }
  return out;
}

function preprocess(file) {
  const img = decodeToPixels(file);
  const scale = 224 / Math.min(img.width, img.height);
  const nw = Math.max(224, Math.round(img.width * scale));
  const nh = Math.max(224, Math.round(img.height * scale));
  const rgb = resizeRGB(img, nw, nh);
  const left = Math.floor((nw - 224) / 2), top = Math.floor((nh - 224) / 2);
  const t = new Float32Array(3 * 224 * 224);
  for (let c = 0; c < 3; c++) {
    for (let y = 0; y < 224; y++) {
      for (let x = 0; x < 224; x++) {
        const src = ((y + top) * nw + (x + left)) * 3 + c;
        t[c * 224 * 224 + y * 224 + x] = (rgb[src] - MEAN[c]) / STD[c];
      }
    }
  }
  return t;
}

const t0 = Date.now();
const model = await CLIPModel.from_pretrained('Xenova/clip-vit-base-patch32', { quantized: true });
const tokenizer = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
console.log('model+tokenizer loaded in', Date.now() - t0, 'ms');

const BLOCKED = [
  'a beautiful scenic landscape photo of nature, mountains, sky, water',
  'a photo with the camera lens covered by a hand or fingers',
  'a close-up photo of fabric, clothing or a bag blocking the view',
  'a blurry, dark or unreadable photo where nothing is visible',
  'a photo of the ground, floor or wall very close to the camera',
];
const SCENE = [
  'a photo of snow covered mountains',
  'a photo of a wide lake or sea',
  'a photo of a forest or grass field',
  'a photo of a sunrise or sunset sky',
  'a photo of a road or highway',
  'a photo of city buildings',
  'a photo of snow',
  'a photo of a sandy beach',
  'a photo of the night sky with stars',
];
const LABELS = [...BLOCKED, ...SCENE];

const tf = await tokenizer(LABELS, { padding: true, truncation: true });
console.log('tokens', tf.input_ids.dims, 'labels', LABELS.length);

const frames = [
  path.join(ROOT, 'work', 'analysis', 'frames', 'REC-0003-A', 'sec_0001.jpg'),
  path.join(ROOT, 'work', 'analysis', 'frames', 'REC-0003-A', 'sec_0060.jpg'),
  path.join(ROOT, 'work', 'analysis', 'frames', 'REC-0004-A', 'sec_0001.jpg'),
  path.join(ROOT, 'work', 'analysis', 'frames', 'REC-0004-A', 'sec_0010.jpg'),
  path.join(ROOT, 'work', 'analysis', 'frames', 'REC-0006-A', 'sec_0005.jpg'),
];
for (const f of frames) {
  const ts = Date.now();
  const pv = preprocess(f);
  const out = await model({
    input_ids: tf.input_ids,
    attention_mask: tf.attention_mask,
    pixel_values: new Tensor('float32', pv, [1, 3, 224, 224]),
  });
  const logits = out.logits_per_image.data;
  const softmax = (arr) => { const m = Math.max(...arr); const e = arr.map(v => Math.exp(v - m)); const s = e.reduce((a, b) => a + b, 0); return e.map(v => v / s); };
  const pb = softmax(logits.slice(0, 5));
  const ps = softmax(logits.slice(5));
  const bestScene = ps.indexOf(Math.max(...ps));
  console.log('\n' + path.basename(path.dirname(f)) + '/' + path.basename(f), (Date.now() - ts) + 'ms');
  BLOCKED.forEach((l, i) => console.log('   ', pb[i].toFixed(3), l.slice(0, 55)));
  SCENE.forEach((l, i) => console.log('    S', ps[i].toFixed(3), l));
  console.log('  -> scene:', SCENE[bestScene], 'p_blocked:', Math.max(pb[1], pb[2], pb[3]).toFixed(3), 'p_closeup:', pb[4].toFixed(3));
}
console.log('\nTOTAL', Date.now() - t0, 'ms');
