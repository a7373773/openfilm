
import subprocess, os, json
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib2"
os.makedirs(TMP, exist_ok=True)

SAMPLES=[("REC-0005-A.mp4",40.0),("REC-0012-A.mp4",60.0),("REC-0017-A.mp4",30.0),("REC-0001-A.mp4",70.0),("REC-0025-A.mp4",75.0),("REC-0024-A.mp4",30.0)]

def grab(f,t,extra,out):
    vf="scale=1920:1080:flags=lanczos"+(((","+extra) if extra else ""))
    cmd=[FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out]
    subprocess.run(cmd,check=True)
    return out

def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    h,w=Y.shape
    c=Y[h//2-60:h//2+60,w//2-60:w//2+60].mean()
    corners=np.mean([Y[0:80,0:80].mean(),Y[0:80,-80:].mean(),Y[-80:,0:80].mean(),Y[-80:,-80:].mean()])
    return dict(p1=round(float(np.percentile(Y,1)),3),p5=round(float(np.percentile(Y,5)),3),
        p50=round(float(np.percentile(Y,50)),3),p95=round(float(np.percentile(Y,95)),3),
        p99=round(float(np.percentile(Y,99)),3),cliphi=round(float((Y>0.99).mean()),3),
        sat=round(float(s.mean()),3),corner=round(float(corners/max(c,1e-6)),3))

LOOKS={
 "none":"",
 "gentle":"eq=contrast=1.05:gamma=1.02:saturation=1.07,colorbalance=rs=-0.015:bs=0.03:rh=0.028:bh=-0.014,curves=all='0/0.012 0.25/0.25 0.5/0.52 0.75/0.78 1/1',vignette=angle=PI/5.5",
 "gentle_novig":"eq=contrast=1.05:gamma=1.02:saturation=1.07,colorbalance=rs=-0.015:bs=0.03:rh=0.028:bh=-0.014,curves=all='0/0.012 0.25/0.25 0.5/0.52 0.75/0.78 1/1'",
 "gentle_vig_only":"vignette=angle=PI/5.5",
 "curves_only":"curves=all='0/0.012 0.25/0.25 0.5/0.52 0.75/0.78 1/1'",
 "eq_only":"eq=contrast=1.05:gamma=1.02:saturation=1.07",
 "cb_only":"colorbalance=rs=-0.015:bs=0.03:rh=0.028:bh=-0.014",
}
for f,t in SAMPLES:
    print("==",f,"t=%.0f"%t)
    for name,extra in LOOKS.items():
        p=grab(f,t,extra,os.path.join(TMP,"%s_%s.png"%(f.split("-")[1],name)))
        print("  %-16s"%name, stats(p))
