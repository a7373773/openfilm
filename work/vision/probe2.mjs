
import path from 'node:path';
import ort from 'onnxruntime-node';
import { env, AutoTokenizer } from '@xenova/transformers';

const ROOT = 'D:\\BaiduSyncdisk\\工作\\PMMaster\\openfilm';
env.allowRemoteModels = false; env.allowLocalModels = true;
env.localModelPath = path.join(ROOT, 'work', 'vision', 'cache');
const tok = await AutoTokenizer.from_pretrained('Xenova/clip-vit-base-patch32');

const modelPath = path.join(ROOT, 'work', 'vision', 'cache', 'Xenova', 'clip-vit-base-patch32', 'onnx', 'model_quantized.onnx');
const s = await ort.InferenceSession.create(modelPath);

const texts = ['a photo of a dog', 'a photo of a snow covered mountain', 'a photo with the camera lens covered by a hand'];
const tf = await tok(texts, { padding: true, truncation: true });
console.log('ids dims', tf.input_ids.dims);
console.log('row0', Array.from(tf.input_ids.data.slice(0, tf.input_ids.dims[1])));
console.log('row1', Array.from(tf.input_ids.data.slice(tf.input_ids.dims[1], 2*tf.input_ids.dims[1])));
console.log('mask0', Array.from(tf.attention_mask.data.slice(0, tf.input_ids.dims[1])));

const dummyImg = new ort.Tensor('float32', new Float32Array(3*224*224), [1,3,224,224]);
const res = await s.run({ input_ids: tf.input_ids, attention_mask: tf.attention_mask, pixel_values: dummyImg });
const te = res.text_embeds;
const D = te.dims[1], N = te.dims[0];
const norm = (a, off) => Math.hypot(...Array.from(a.slice(off, off+D)));
const cos = (a, i, b, j) => { let s2 = 0; for (let k = 0; k < D; k++) s2 += a[i*D+k]*b[j*D+k]; return s2/(norm(a,i*D)*norm(b,j*D)); };
console.log('\ntext embed norms:', [0,1,2].map(i => norm(te.data, i*D).toFixed(3)).join(' '));
console.log('cos(t0,t1)=', cos(te.data,0,te.data,1).toFixed(4));
console.log('cos(t0,t2)=', cos(te.data,0,te.data,2).toFixed(4));
console.log('cos(t1,t2)=', cos(te.data,1,te.data,2).toFixed(4));
for (let i = 0; i < N; i++) {
  console.log('t' + i, 'first10', Array.from(te.data.slice(i*D, i*D+10)).map(v=>v.toFixed(4)).join(' '));
}
// logits from model for these 3 texts with a real image
import fs from 'node:fs';
import jpeg from 'jpeg-js';
const MEAN = [0.48145466,0.4578275,0.40821073], STD=[0.26862954,0.26130258,0.27577711];
function prep(file){
  const img = jpeg.decode(fs.readFileSync(file), {useTArray:true, formatAsRGBA:true});
  const scale = 224/Math.min(img.width,img.height);
  const nw = Math.max(224, Math.round(img.width*scale)), nh = Math.max(224, Math.round(img.height*scale));
  const {width:W, height:H, data} = img;
  const rgb = new Float32Array(nw*nh*3);
  for (let y=0;y<nh;y++){ let sy=((y+0.5)*H/nh)-0.5; if(sy<0)sy=0; const y0=Math.min(H-1,Math.floor(sy)), y1=Math.min(H-1,y0+1), fy=sy-y0;
    for(let x=0;x<nw;x++){ let sx=((x+0.5)*W/nw)-0.5; if(sx<0)sx=0; const x0=Math.min(W-1,Math.floor(sx)), x1=Math.min(W-1,x0+1), fx=sx-x0;
      const i00=(y0*W+x0)*4,i01=(y0*W+x1)*4,i10=(y1*W+x0)*4,i11=(y1*W+x1)*4,o=(y*nw+x)*3;
      for(let c=0;c<3;c++) rgb[o+c]=((data[i00+c]*(1-fx)+data[i01+c]*fx)*(1-fy)+(data[i10+c]*(1-fx)+data[i11+c]*fx)*fy)/255; } }
  const left=Math.floor((nw-224)/2), top=Math.floor((nh-224)/2);
  const t=new Float32Array(3*224*224);
  for(let c=0;c<3;c++)for(let y=0;y<224;y++)for(let x=0;x<224;x++) t[c*224*224+y*224+x]=(rgb[((y+top)*nw+(x+left))*3+c]-MEAN[c])/STD[c];
  return t;
}
const f = path.join(ROOT,'work','analysis','frames','REC-0018-A','sec_0010.jpg');
const r2 = await s.run({ input_ids: tf.input_ids, attention_mask: tf.attention_mask, pixel_values: new ort.Tensor('float32', prep(f), [1,3,224,224]) });
console.log('\nreal image logits_per_image:', Array.from(r2.logits_per_image.data).map(v=>v.toFixed(3)).join(' '));
const ie = r2.image_embeds;
console.log('image norm', norm(ie.data,0).toFixed(3));
console.log('cos(img, t0/t1/t2):', [0,1,2].map(i => cos(ie.data,0,te.data,i).toFixed(4)).join(' '));
