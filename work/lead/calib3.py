
import subprocess, os, json
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib3"
os.makedirs(TMP, exist_ok=True)
SAMPLES=[("REC-0005-A.mp4",40.0),("REC-0012-A.mp4",60.0),("REC-0017-A.mp4",30.0),("REC-0001-A.mp4",70.0),("REC-0025-A.mp4",75.0),("REC-0024-A.mp4",30.0)]
def grab(f,t,extra,out):
    vf="scale=1920:1080:flags=lanczos"+(((","+extra) if extra else ""))
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],check=True)
    return out
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    h,w=Y.shape; c=Y[h//2-60:h//2+60,w//2-60:w//2+60].mean()
    corners=np.mean([Y[0:80,0:80].mean(),Y[0:80,-80:].mean(),Y[-80:,0:80].mean(),Y[-80:,-80:].mean()])
    return dict(p1=round(float(np.percentile(Y,1)),3),p50=round(float(np.percentile(Y,50)),3),
        p90=round(float(np.percentile(Y,90)),3),p95=round(float(np.percentile(Y,95)),3),
        cliphi=round(float((Y>0.99).mean()),3),sat=round(float(s.mean()),3),corner=round(float(corners/max(c,1e-6)),3))
ROLL="curves=all='0/0.008 0.2/0.205 0.5/0.53 0.8/0.79 0.9/0.855 1/0.94'"
ROLL_S="curves=all='0/0.01 0.25/0.255 0.5/0.525 0.8/0.80 1/0.92'"
SAT="eq=saturation=1.07:contrast=1.02:gamma=1.0"
CB="colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012"
LOOKS={
 "L1_roll_v36": ROLL+","+SAT+","+CB+",vignette=angle=PI/3.6",
 "L2_roll_v32": ROLL+","+SAT+","+CB+",vignette=angle=PI/3.2",
 "L3_roll_novig": ROLL+","+SAT+","+CB,
 "L4_strongroll_v36": ROLL_S+",eq=saturation=1.08:contrast=1.03,"+CB+",vignette=angle=PI/3.6",
 "L5_plain": SAT+","+CB,
}
agg={k:[] for k in LOOKS}
for f,t in SAMPLES:
    base=None
    for name,extra in LOOKS.items():
        p=grab(f,t,extra,os.path.join(TMP,"%s_%s.png"%(f[4:8],name)))
        st=stats(p); agg[name].append(st)
    b=stats(os.path.join(TMP,"%s_base.png"%(f[4:8])) if False else grab(f,t,"",os.path.join(TMP,"%s_base.png"%f[4:8])))
    print("==",f,"  BASE",b)
    for name in LOOKS:
        s=agg[name][-1]
        print("  %-18s dp50=%+.3f p95=%.3f cliphi=%.3f satx%.2f corner=%.2f" % (
            name, s["p50"]-b["p50"], s["p95"], s["cliphi"], s["sat"]/max(b["sat"],1e-6), s["corner"]))
print("\n--- means ---")
for name in LOOKS:
    m={k: np.mean([s[k] for s in agg[name]]) for k in agg[name][0]}
    print("%-18s p50=%.3f p95=%.3f cliphi=%.3f sat=%.3f corner=%.2f" % (name,m["p50"],m["p95"],m["cliphi"],m["sat"],m["corner"]))
