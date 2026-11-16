
import subprocess, os, re
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
import sys
P = sys.argv[1] if len(sys.argv) > 1 else r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\render\hike_v3.mp4"
out = subprocess.run([FF,"-hide_banner","-i",P],capture_output=True).stderr.decode("utf-8","replace")
print("\n".join([l for l in out.splitlines() if "Duration" in l or "Stream #" in l])[:600])
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\render\vf"; os.makedirs(TMP, exist_ok=True)
for f in os.listdir(TMP): os.remove(os.path.join(TMP,f))
subprocess.run([FF,"-v","error","-y","-i",P,"-vf","fps=1,scale=480:-2","-q:v","3",os.path.join(TMP,"f_%04d.jpg")],check=True)
rows=[]
for f in sorted(os.listdir(TMP)):
    a=np.asarray(Image.open(os.path.join(TMP,f)).convert("RGB")).astype(np.float32)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    gx=np.diff(Y,axis=1); gy=np.diff(Y,axis=0)
    mx=a.max(axis=2); mn=a.min(axis=2)
    sat=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    rows.append((float(Y.mean()), float(gx.var()+gy.var()), float(sat.mean())))
Y=[r[0] for r in rows]; S=[r[1] for r in rows]; A=[r[2] for r in rows]
print("samples", len(rows))
print("luma  min=%.1f p10=%.1f med=%.1f max=%.1f"%(min(Y),np.percentile(Y,10),np.median(Y),max(Y)))
print("sharp min=%.1f p10=%.1f med=%.1f"%(min(S),np.percentile(S,10),np.median(S)))
print("sat   min=%.2f p10=%.2f med=%.2f"%(min(A),np.percentile(A,10),np.median(A)))
bad=[(i+1,round(Y[i],1),round(S[i],1)) for i in range(len(rows)) if S[i]<40 or Y[i]<35]
print("suspect seconds:", bad[:12])
lo=[i+1 for i in range(len(rows)) if Y[i]<70]
print("dark seconds count:", len(lo), lo[:20])
