
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib8"
os.makedirs(TMP, exist_ok=True)
SHOTS=[("REC-0005-A.mp4",41.5),("REC-0012-A.mp4",60.5),("REC-0017-A.mp4",30.0),("REC-0001-A.mp4",70.0),("REC-0025-A.mp4",75.0)]
LV="colorlevels=rimin=0.05:rimax=0.97:gimin=0.05:gimax=0.97:bimin=0.05:bimax=0.97"
CURVE="curves=all='0/0.010 0.25/0.255 0.5/0.525 0.80/0.800 1/0.920'"
CB="colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012"
def mk(sat,vib):
    return ("format=yuv444p10le,"+LV+","+CURVE+",format=yuv420p,"
            "eq=saturation=%.2f:contrast=1.02,vibrance=%.2f,"%(sat,vib)+CB)
V={"A_s1.00v0.00":mk(1.00,0.0),"B_s1.03v0.08":mk(1.03,0.08),"C_s1.05v0.16":mk(1.05,0.16),"D_s1.08v0.26":mk(1.08,0.26)}
def grab(f,t,extra,out):
    vf="scale=1920:1080:flags=lanczos"+(((","+extra) if extra else ""))
    p=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],capture_output=True)
    return (out if p.returncode==0 else None), p.stderr.decode("utf-8","replace")[-300:]
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2);mn=a.min(axis=2);s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    return dict(p50=float(np.percentile(Y,50)),p95=float(np.percentile(Y,95)),
       cliphi=float((Y>0.99).mean()),clip_lo=float((Y<0.012).mean()),sat=float(s.mean()),
       sathigh=float((s>0.92).mean()),Y=float(Y.mean()))
base={};var={k:[] for k in V}
for f,t in SHOTS:
    b,_=grab(f,t,"",os.path.join(TMP,"%s_b.png"%f[4:8])); base[f]=stats(b)
    for k,v in V.items():
        p,err=grab(f,t,v,os.path.join(TMP,"%s_%s.png"%(f[4:8],k)))
        if p is None: print("ERR",k,err); continue
        var[k].append(stats(p))
names=[s[0] for s in SHOTS]
print("%-14s %6s %6s %6s %7s %8s %8s %8s"%("variant","satx","Yx","p95","cliphi","clip_lo","sathigh","p50x"))
for k in V:
    if not var[k]: continue
    satx=np.mean([var[k][i]["sat"]/base[names[i]]["sat"] for i in range(len(SHOTS))])
    Yx=np.mean([var[k][i]["Y"]/base[names[i]]["Y"] for i in range(len(SHOTS))])
    p50x=np.mean([var[k][i]["p50"]/base[names[i]]["p50"] for i in range(len(SHOTS))])
    m={kk: np.mean([s[kk] for s in var[k]]) for kk in var[k][0]}
    print("%-14s %6.3f %6.3f %6.3f %7.4f %8.4f %8.4f %8.3f"%(k,satx,Yx,m["p95"],m["cliphi"],m["clip_lo"],m["sathigh"],p50x))
print("\nbase: p95=%.3f cliphi=%.4f clip_lo=%.4f sathigh=%.4f Y=%.3f"%(
  np.mean([b["p95"] for b in base.values()]),np.mean([b["cliphi"] for b in base.values()]),
  np.mean([b["clip_lo"] for b in base.values()]),np.mean([b["sathigh"] for b in base.values()]),
  np.mean([b["Y"] for b in base.values()])))
