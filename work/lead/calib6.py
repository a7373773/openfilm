
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib6"
os.makedirs(TMP, exist_ok=True)
SHOTS=[("REC-0005-A.mp4",41.5),("REC-0012-A.mp4",60.5),("REC-0017-A.mp4",30.0),("REC-0001-A.mp4",70.0),("REC-0025-A.mp4",75.0)]
LV="colorlevels=rimin=0.06:rimax=0.95:gimin=0.06:gimax=0.95:bimin=0.06:bimax=0.95"
CURVE="curves=all='0/0.010 0.25/0.255 0.5/0.525 0.80/0.800 1/0.920'"
CB="colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012"
def mk(sat,vib):
    return "format=yuv444p10le,"+LV+","+CURVE+",eq=saturation=%.2f:contrast=1.03,vibrance=%.2f,"%(sat,vib)+CB+",format=yuv420p"
VARIANTS={"S1.00V0.00":mk(1.00,0.0),"S1.02V0.10":mk(1.02,0.10),"S1.05V0.18":mk(1.05,0.18),"S1.08V0.28":mk(1.08,0.28),"S1.12V0.40":mk(1.12,0.40)}
def grab(f,t,extra,out):
    vf="scale=1920:1080:flags=lanczos"+(((","+extra) if extra else ""))
    p=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],capture_output=True)
    return (out if p.returncode==0 else None), p.stderr.decode("utf-8","replace")[-300:]
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    return dict(p50=float(np.percentile(Y,50)),p95=float(np.percentile(Y,95)),cliphi=float((Y>0.99).mean()),
                clip_lo=float((Y<0.01).mean()),sat=float(s.mean()),
                sathigh=float((s>0.9).mean()))
base={}; var={k:[] for k in VARIANTS}
for f,t in SHOTS:
    b,_=grab(f,t,"",os.path.join(TMP,"%s_b.png"%f[4:8])); base[f]=stats(b)
    for k,v in VARIANTS.items():
        p,err=grab(f,t,v,os.path.join(TMP,"%s_%s.png"%(f[4:8],k)))
        if p is None: print("ERR",k,err); continue
        var[k].append(stats(p))
print("%-12s %8s %8s %8s %8s %8s %8s"%("variant","satx","p50x","p95","cliphi","sathigh","clip_lo"))
for k in VARIANTS:
    if not var[k]: continue
    satx=np.mean([var[k][i]["sat"]/base[f]["sat"] for i,f in enumerate([s[0] for s in SHOTS])])
    p50x=np.mean([var[k][i]["p50"]/base[f]["p50"] for i,f in enumerate([s[0] for s in SHOTS])])
    m={kk: np.mean([s[kk] for s in var[k]]) for kk in var[k][0]}
    print("%-12s %8.3f %8.3f %8.3f %8.3f %8.3f %8.4f"%(k,satx,p50x,m["p95"],m["cliphi"],m["sathigh"],m["clip_lo"]))
print()
print("base means: satx=1.000 p50x=1.000 p95=%.3f cliphi=%.3f sathigh=%.3f clip_lo=%.4f"%(
  np.mean([b["p95"] for b in base.values()]), np.mean([b["cliphi"] for b in base.values()]),
  np.mean([b["sathigh"] for b in base.values()]), np.mean([b["clip_lo"] for b in base.values()])))
