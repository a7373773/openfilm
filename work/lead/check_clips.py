
import subprocess, os, json
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
C = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\clips"
for f in ["shot_00.mp4","shot_01.mp4"]:
    p=os.path.join(C,f)
    r=subprocess.run([FF,"-v","error","-i",p,"-f","null","-"],capture_output=True)
    out=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    import re
    dur=re.search(r"Duration: (\S+),",out).group(1)
    lines=[l for l in out.splitlines() if "Stream #0:0" in l]
    # decode all frames to count
    n=subprocess.run([FF,"-v","error","-i",p,"-f","null","-"],capture_output=True).stderr.decode("utf-8","replace")
    print(f,"dur",dur,lines[0][:90] if lines else "")
# stat graded vs source
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2); mn=a.min(axis=2); s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    return dict(p1=round(float(np.percentile(Y,1)),3),p50=round(float(np.percentile(Y,50)),3),
      p95=round(float(np.percentile(Y,95)),3),cliphi=round(float((Y>0.99).mean()),3),
      sat=round(float(s.mean()),3),sat_p1=round(float(np.percentile(s,1)),3))
TMP=r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib5"
os.makedirs(TMP,exist_ok=True)
for src,t,out in [("REC-0005-A.mp4",41.5,"a.png"),("REC-0012-A.mp4",60.8,"b.png")]:
    subprocess.run([FF,"-v","error","-y","-i",os.path.join(C,"shot_00.mp4" if src.startswith("REC-0005") else "shot_01.mp4"),"-vf","select=eq(n\\,45)","-frames:v","1",os.path.join(TMP,out)],check=True)
    print(out,"GRADED",stats(os.path.join(TMP,out)))
