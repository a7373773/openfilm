
# -*- coding: utf-8 -*-
"""Calibrate the grade: measure luma/sat/vignette before and after applying ffmpeg filter chain."""
import subprocess, os, sys, json
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib"
os.makedirs(TMP, exist_ok=True)

SAMPLES = [("REC-0005-A.mp4", 40.0), ("REC-0012-A.mp4", 60.0), ("REC-0017-A.mp4", 30.0), ("REC-0001-A.mp4", 70.0)]

def grab(f, t, out):
    cmd=[FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),
         "-frames:v","1","-vf","scale=1920:1080:flags=lanczos","-q:v","2",out]
    subprocess.run(cmd,check=True)
    return out

def apply(filt, inp, out):
    cmd=[FF,"-v","error","-y","-i",inp,"-vf",filt,"-frames:v","1","-q:v","2",out]
    subprocess.run(cmd,check=True)
    return out

def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); v=mx
    s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    h,w=Y.shape
    c=Y[h//2-60:h//2+60, w//2-60:w//2+60].mean()
    corners=np.mean([Y[0:80,0:80].mean(),Y[0:80,-80:].mean(),Y[-80:,0:80].mean(),Y[-80:,-80:].mean()])
    return {"p1":float(np.percentile(Y,1)),"p5":float(np.percentile(Y,5)),"p50":float(np.percentile(Y,50)),
            "p95":float(np.percentile(Y,95)),"p99":float(np.percentile(Y,99)),
            "clip_low":float((Y<0.01).mean()),"clip_hi":float((Y>0.99).mean()),
            "sat":float(s.mean()),"corner_ratio":float(corners/max(c,1e-6))}

LOOKS = {
 "none": "",
 "A_gentle": "eq=contrast=1.06:gamma=1.02:saturation=1.08,colorbalance=rs=-0.015:bs=0.030:rh=0.030:bh=-0.015,curves=master='0/0.015 0.25/0.255 0.5/0.525 0.75/0.785 1/1',vignette=angle=PI/5.5",
 "B_film": "eq=contrast=1.10:gamma=1.03:saturation=1.12,colorbalance=rs=-0.025:bs=0.045:rh=0.035:bh=-0.020,curves=master='0/0.022 0.22/0.225 0.5/0.535 0.78/0.815 1/1',vignette=angle=PI/5.0",
 "C_strong": "eq=contrast=1.16:gamma=1.05:saturation=1.18,colorbalance=rs=-0.04:bs=0.06:rh=0.05:bh=-0.03,curves=master='0/0.03 0.2/0.21 0.5/0.55 0.8/0.84 1/1',vignette=angle=PI/4.5",
}
res={}
for i,(f,t) in enumerate(SAMPLES):
    base=grab(f,t,os.path.join(TMP,"s%d_base.jpg"%i))
    res[f]={}
    print("==",f,"t=%.0f"%t)
    print("   none      ", stats(base))
    for name,flt in LOOKS.items():
        if not flt: continue
        p=apply(flt,base,os.path.join(TMP,"s%d_%s.jpg"%(i,name)))
        st=stats(p); res[f][name]=st
        print("   %-10s"%name, st)
json.dump(res, open(os.path.join(TMP,"calib.json"),"w"), indent=1)
