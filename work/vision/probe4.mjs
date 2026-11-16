
import path from 'node:path';
import ort from 'onnxruntime-node';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const modelPath = path.join(ROOT, 'work', 'vision', 'cache', 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const s = await ort.InferenceSession.create(modelPath);

// build texts: tokenize ourselves is hard; instead reuse a fixed mapping by running one text at a time
// We only have token ids we can approximate. Use single-label inference: run each label separately.
// We cannot tokenize without transformers tokenizer -> import it.
const { env, AutoTokenizer } = await import('@xenova/transformers');
env.allowRemoteModels = false; env.allowLocalModels = true;
env.localModelPath = path.join(ROOT, 'work', 'vision', 'cache');
const tok = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');

const LABELS = ['a photo of a plain black screen', 'a photo of a plain white screen', 'a photo of colorful random noise', 'a photo of a checkerboard pattern'];
const tf = await tok(LABELS, { padding: true, truncation: true });
const idsN = tf.input_ids.dims[1];
const ids = new ort.Tensor('int64', tf.input_ids.data, [LABELS.length, idsN]);
const mask = new ort.Tensor('int64', tf.attention_mask.data, [LABELS.length, idsN]);

function mk(fn) { const d = new Float32Array(3*224*224); for (let c=0;c<3;c++) for (let y=0;y<224;y++) for (let x=0;x<224;x++) d[c*224*224+y*224+x] = fn(c,x,y); return new ort.Tensor('float32', d, [1,3,224,224]); }
const imgs = {
  black: mk(() => -2.0),
  white: mk(() => 2.0),
  noise: mk(() => Math.random()*4-2),
  checker: mk((c,x,y) => ((x>>3)+(y>>3)) % 2 ? 2 : -2),
};
const sm = (a) => { const m = Math.max(...a); const e = a.map(v=>Math.exp(v-m)); const t = e.reduce((x,y)=>x+y,0); return e.map(v=>v/t); };
for (const [k, t] of Object.entries(imgs)) {
  const r = await s.run({ input_ids: ids, attention_mask: mask, pixel_values: t });
  const lg = Array.from(r.logits_per_image.data);
  console.log(k.padEnd(8), 'logits:', lg.map(v=>v.toFixed(2)).join(' '), ' softmax:', sm(lg).map(v=>v.toFixed(3)).join(' '));
}
console.log('\nlabels:', LABELS.join(' | '));
// also: only 2 labels highly distinct
const L2 = ['a photo of a bright white blank image', 'a photo of a dark black image'];
const tf2 = await tok(L2, { padding: true, truncation: true });
const ids2 = new ort.Tensor('int64', tf2.input_ids.data, [2, tf2.input_ids.dims[1]]);
const mask2 = new ort.Tensor('int64', tf2.attention_mask.data, [2, tf2.input_ids.dims[1]]);
for (const [k, t] of Object.entries(imgs)) {
  const r = await s.run({ input_ids: ids2, attention_mask: mask2, pixel_values: t });
  const lg = Array.from(r.logits_per_image.data);
  console.log('2way', k.padEnd(8), 'logits:', lg.map(v=>v.toFixed(2)).join(' '), ' softmax:', sm(lg).map(v=>v.toFixed(3)).join(' '));
}
