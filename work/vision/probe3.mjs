
import path from 'node:path';
import ort from 'onnxruntime-node';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
const modelPath = path.join(ROOT, 'work', 'vision', 'cache', 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const s = await ort.InferenceSession.create(modelPath);
const ids = new ort.Tensor('int64', new BigInt64Array([49406n,320n,1125n,539n,320n,1929n,49407n,49407n,49407n]), [1, 9]);
const mask = new ort.Tensor('int64', new BigInt64Array([1n,1n,1n,1n,1n,1n,1n,0n,0n]), [1, 9]);

function mk(fn) { const d = new Float32Array(3*224*224); for (let c=0;c<3;c++) for (let y=0;y<224;y++) for (let x=0;x<224;x++) d[c*224*224+y*224+x] = fn(c,x,y); return new ort.Tensor('float32', d, [1,3,224,224]); }
const imgs = {
  black: mk(() => -2.0),
  white: mk(() => 2.0),
  checker: mk((c,x,y) => ((x>>3)+(y>>3)) % 2 ? 2 : -2),
  hgrad: mk((c,x) => (x/223)*4-2),
  noise: mk(() => Math.random()*4-2),
  redish: mk((c) => c===0 ? 1.6 : -1.6),
  bluish: mk((c) => c===2 ? 1.6 : -1.6),
};
const embs = {};
for (const [k, t] of Object.entries(imgs)) {
  const r = await s.run({ input_ids: ids, attention_mask: mask, pixel_values: t });
  embs[k] = r.image_embeds.data;
  console.log(k.padEnd(8), 'logits:', Array.from(r.logits_per_image.data).map(v=>v.toFixed(2)).join(' '), 'emb[:5]', Array.from(r.image_embeds.data.slice(0,5)).map(v=>v.toFixed(3)).join(' '));
}
const keys = Object.keys(imgs);
const cos = (a,b) => { let s2=0; for (let i=0;i<512;i++) s2+=a[i]*b[i]; return s2; };
console.log('\npairwise cos of image_embeds:');
console.log('        ' + keys.map(k=>k.slice(0,6).padStart(7)).join(''));
for (const a of keys) console.log(a.padEnd(8) + keys.map(b => cos(embs[a],embs[b]).toFixed(3).padStart(7)).join(''));
