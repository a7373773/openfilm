
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib4"
os.makedirs(TMP, exist_ok=True)
SAMPLES=[("REC-0005-A.mp4",40.0),("REC-0012-A.mp4",60.0),("REC-0017-A.mp4",30.0),("REC-0001-A.mp4",70.0),("REC-0024-A.mp4",30.0)]
def grab(f,t,extra,out):
    vf="scale=1920:1080:flags=lanczos"+(((","+extra) if extra else ""))
    p=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],capture_output=True)
    return out if p.returncode==0 else None, p.stderr.decode("utf-8","replace")[-400:]
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    # saturation of low-sat pixels only (vibrance check) and overall
    low=s<0.25
    return dict(p50=round(float(np.percentile(Y,50)),3),p95=round(float(np.percentile(Y,95)),3),
      cliphi=round(float((Y>0.99).mean()),3),sat=round(float(s.mean()),3),
      satlow=round(float(s[low].mean()) if low.sum() else 0,3), satfrac_lowsat=round(float(low.mean()),3))
CURVE="curves=all='0/0.01 0.25/0.255 0.5/0.525 0.8/0.80 1/0.92'"
CB="colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012"
LOOKS={
 "V0": CURVE+",eq=saturation=1.06:contrast=1.03,"+CB,
 "V1": CURVE+",eq=saturation=1.04:contrast=1.03,vibrance=0.35,"+CB,
 "V2": CURVE+",eq=saturation=1.03:contrast=1.03,vibrance=0.55,"+CB,
 "V3_10bit": "format=yuv444p10le,"+CURVE+",eq=saturation=1.04:contrast=1.03,vibrance=0.35,"+CB+",format=yuv420p",
 "V4_10bit_novib": "format=yuv444p10le,"+CURVE+",eq=saturation=1.08:contrast=1.03,"+CB+",format=yuv420p",
}
for f,t in SAMPLES:
    b,_=grab(f,t,"",os.path.join(TMP,"%s_b.png"%f[4:8]))
    print("==",f,"BASE",stats(b))
    for k,v in LOOKS.items():
        p,err=grab(f,t,v,os.path.join(TMP,"%s_%s.png"%(f[4:8],k)))
        if p is None: print("  %-14s ERR %s"%(k,err)); continue
        print("  %-14s"%k, stats(p))
