
import fs from 'node:fs';
import path from 'node:path';
import jpeg from 'jpeg-js';
import { env, CLIPModel, AutoTokenizer, Tensor } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
env.allowRemoteModels = false; env.allowLocalModels = true;
env.localModelPath = path.join(ROOT, 'work', 'vision', 'cache');
const MEAN = [0.48145466, 0.4578275, 0.40821073];
const STD = [0.26862954, 0.26130258, 0.27577711];

function preprocess(file) {
  const img = jpeg.decode(fs.readFileSync(file), { useTArray: true, formatAsRGBA: true });
  const scale = 224 / Math.min(img.width, img.height);
  const nw = Math.max(224, Math.round(img.width * scale)), nh = Math.max(224, Math.round(img.height * scale));
  const { width: W, height: H, data } = img;
  const rgb = new Float32Array(nw * nh * 3);
  for (let y = 0; y < nh; y++) {
    let sy = ((y + 0.5) * H / nh) - 0.5; if (sy < 0) sy = 0;
    let y0 = Math.min(H - 1, Math.floor(sy)), y1 = Math.min(H - 1, y0 + 1), fy = sy - y0;
    for (let x = 0; x < nw; x++) {
      let sx = ((x + 0.5) * W / nw) - 0.5; if (sx < 0) sx = 0;
      let x0 = Math.min(W - 1, Math.floor(sx)), x1 = Math.min(W - 1, x0 + 1), fx = sx - x0;
      const i00 = (y0 * W + x0) * 4, i01 = (y0 * W + x1) * 4, i10 = (y1 * W + x0) * 4, i11 = (y1 * W + x1) * 4;
      const o = (y * nw + x) * 3;
      for (let c = 0; c < 3; c++) rgb[o + c] = ((data[i00+c]*(1-fx)+data[i01+c]*fx)*(1-fy) + (data[i10+c]*(1-fx)+data[i11+c]*fx)*fy) / 255;
    }
  }
  const left = Math.floor((nw - 224) / 2), top = Math.floor((nh - 224) / 2);
  const t = new Float32Array(3 * 224 * 224);
  for (let c = 0; c < 3; c++) for (let y = 0; y < 224; y++) for (let x = 0; x < 224; x++)
    t[c*224*224 + y*224 + x] = (rgb[((y+top)*nw + (x+left))*3 + c] - MEAN[c]) / STD[c];
  return { t, img };
}

const model = await CLIPModel.from_pretrained('Xenova/clip-vit-base-patch32', { quantized: true });
const tokenizer = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');
console.log('model version/outputs keys:', Object.keys(model.model ? model.model : {}), Object.keys(model));
console.log('config:', JSON.stringify({ p: model.config?.projection_dim, v: model.config?.vision_config?.hidden_size, t: model.config?.text_config?.hidden_size }));

const LABELS = [
  'a photo of a dog','a photo of a cat','a photo of a mountain landscape',
  'a photo of a hand covering the camera lens','a photo of a blank grey wall',
  'a photo of a red car','a photo of a page of text',
  'a photo of a beautiful scenic nature landscape with sky and water',
  'a close-up of dark fabric','a blurry meaningless image with no content',
];
const tf = await tokenizer(LABELS, { padding: true, truncation: true });
console.log('ids dims', tf.input_ids.dims, 'first rows:', tf.input_ids.data.slice(0, 20), 'attn', tf.attention_mask.data.slice(0, 20));
const tout = await model.get_text_features({ input_ids: tf.input_ids, attention_mask: tf.attention_mask });
const te = tout; // Tensor [N,512]
console.log('text_embeds dims', te.dims, 'norm0', Math.hypot(...te.data.slice(0, 512)));
const dot = (a, aoff, b, boff, d) => { let s = 0; for (let i = 0; i < d; i++) s += a[aoff+i]*b[boff+i]; return s; };
const D = te.dims[1];
const sims01 = [];
for (let j = 1; j < te.dims[0]; j++) sims01.push(dot(te.data, 0, te.data, j*D, D));
console.log('cos(text0, textj):', sims01.map(v => v.toFixed(3)).join(' '));

const files = [
  path.join(ROOT,'work','analysis','frames','REC-0015-A','sec_0010.jpg'),
  path.join(ROOT,'work','analysis','frames','REC-0018-A','sec_0010.jpg'),
  path.join(ROOT,'work','analysis','frames','REC-0004-A','sec_0001.jpg'),
];
for (const f of files) {
  const { t, img } = preprocess(f);
  let mean = 0; for (let i = 0; i < t.length; i++) mean += t[i];
  const out = await model({ input_ids: tf.input_ids, attention_mask: tf.attention_mask, pixel_values: new Tensor('float32', t, [1,3,224,224]) });
  console.log('\n=== ' + f.split('\\').slice(-2).join('/') + ' size=' + img.width + 'x' + img.height + ' pixelMean=' + (mean/t.length).toFixed(3));
  console.log('out keys:', Object.keys(out), 'logits dims', out.logits_per_image?.dims);
  const lg = out.logits_per_image.data;
  const order = [...lg.keys()].sort((a,b)=>lg[b]-lg[a]);
  for (const i of order) console.log('   logit=' + lg[i].toFixed(2) + '  ' + LABELS[i]);
  if (out.image_embeds) {
    console.log('   image_embeds norm', Math.hypot(...out.image_embeds.data.slice(0,512)).toFixed(3));
  }
}
