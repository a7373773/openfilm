
import path from 'node:path';
import ort from 'onnxruntime-node';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const modelPath = path.join(ROOT, 'work', 'vision', 'cache', 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const s = await ort.InferenceSession.create(modelPath);
console.log('inputs:', s.inputNames);
console.log('outputs:', s.outputNames);

// synthetic: 2 text batches (2 labels each), 2 different random images
const seq = 8;
const mkIds = (arr) => { const d = new BigInt64Array(seq * arr.length); for (let i = 0; i < arr.length; i++) for (let j = 0; j < seq; j++) d[i*seq+j] = BigInt(j < arr[i].length ? arr[i][j] : 49407); return new ort.Tensor('int64', d, [arr.length, seq]); };
const mask = (n, len) => { const d = new BigInt64Array(n*seq); for (let i = 0; i < n; i++) for (let j = 0; j < seq; j++) d[i*seq+j] = BigInt(j < len ? 1 : 0); return new ort.Tensor('int64', d, [n, seq]); };

const ids = mkIds([[49406, 320, 1125, 539, 320, 1929, 49407], [49406, 320, 1125, 539, 320, 4155, 49407]]); // "a photo of a dog" / "a photo of a mountain"(guess)
const m = mask(2, 7);

const mkImg = (fill) => { const d = new Float32Array(3*224*224); for (let c = 0; c < 3; c++) for (let i = 0; i < 224*224; i++) d[c*224*224+i] = fill(c); return new ort.Tensor('float32', d, [1,3,224,224]); };
const randImg = () => { const d = new Float32Array(3*224*224); for (let i = 0; i < d.length; i++) d[i] = Math.random()*2-1; return new ort.Tensor('float32', d, [1,3,224,224]); };
const stripe = (flip) => { const d = new Float32Array(3*224*224); for (let y = 0; y < 224; y++) for (let x = 0; x < 224; x++) for (let c = 0; c < 3; c++) d[c*224*224+y*224+x] = ((x >> 4) % 2 === flip ? 1 : -1) * (1 - c*0.2); return new ort.Tensor('float32', d, [1,3,224,224]); };

const outs = {};
for (const [name, img] of [['red', mkImg(c => c === 0 ? 1 : (c===1? -1 : -1))], ['random', randImg()], ['stripeA', stripe(0)], ['stripeB', stripe(1)]]) {
  const res = await s.run({ input_ids: ids, attention_mask: m, pixel_values: img });
  const lg = res.logits_per_image.data;
  outs[name] = lg;
  console.log(name, 'logits:', Array.from(lg).map(v => v.toFixed(3)).join(' '));
  if (res.image_embeds) console.log('   img_emb[dims]', res.image_embeds.dims, 'first5', Array.from(res.image_embeds.data.slice(0,5)).map(v=>v.toFixed(3)));
  if (res.text_embeds) console.log('   txt_emb[dims]', res.text_embeds.dims, 'first5', Array.from(res.text_embeds.data.slice(0,5)).map(v=>v.toFixed(3)));
  console.log('   keys:', Object.keys(res));
}
// difference between frames
const a = outs.red, b = outs.stripeA;
let d = 0; for (let i = 0; i < a.length; i++) d += Math.abs(a[i]-b[i]);
console.log('\nsum |logits(red) - logits(stripeA)| =', d.toFixed(4), ' values:', Array.from(a).concat(Array.from(b)).map(v=>v.toFixed(3)).join(' '));
