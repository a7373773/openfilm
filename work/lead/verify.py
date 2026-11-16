
# -*- coding: utf-8 -*-
"""Verify a rendered montage: technical + per-second picture sanity."""
import subprocess, os, sys, json
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"

def probe(p):
    out = subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    import re
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    secs = int(dur.group(1))*3600+int(dur.group(2))*60+float(dur.group(3)) if dur else None
    return out, secs

def frames(p, dirout, fps=1):
    os.makedirs(dirout, exist_ok=True)
    for f in os.listdir(dirout): os.remove(os.path.join(dirout,f))
    subprocess.run([FF,"-v","error","-y","-i",p,"-vf","fps=%d,scale=480:-2"%fps,"-q:v","3",os.path.join(dirout,"f_%04d.jpg")],check=True)
    return sorted(os.listdir(dirout))

def stats(path):
    a=np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    gx=np.diff(Y,axis=1); gy=np.diff(Y,axis=0)
    sharp=float(gx.var()+gy.var())
    mx=a.max(axis=2);mn=a.min(axis=2)
    sat=float(np.where(mx>0,(mx-mn)/(mx+1e-6),0).mean())
    return dict(luma=float(Y.mean()), lumastd=float(Y.std()), sharp=sharp, sat=sat,
                dark=float((Y<28).mean()), bright=float((Y>235).mean()))

p = sys.argv[1]
out,secs = probe(p)
print("DURATION: %.2f s" % secs)
for line in out.splitlines():
    if "Stream #" in line: print("  ", line.strip()[:120])
d = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\render\_vframe"
fl = frames(p, d)
rows=[stats(os.path.join(d,f)) for f in fl]
print("\nper-second picture stats over %d samples:" % len(rows))
for k in ("luma","sharp","sat"):
    v=[r[k] for r in rows]
    print("  %-10s min=%7.1f  p10=%7.1f  med=%7.1f  max=%7.1f"%(k,min(v),np.percentile(v,10),np.median(v),max(v)))
bad=[(i+1,r) for i,r in enumerate(rows) if r["sharp"]<40 or r["luma"]<45 or r["luma"]>225 or r["dark"]>0.5]
print("\nsuspect seconds (sharp<40 or extreme luma):", [(i, round(r["sharp"],1), round(r["luma"],1)) for i,r in bad][:20])
# black frame check at start/end
print("\nfirst/last frames:", json.dumps({k:round(v,2) for k,v in rows[0].items()}), json.dumps({k:round(v,2) for k,v in rows[-1].items()}))
