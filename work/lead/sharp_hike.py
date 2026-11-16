
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\render\sharpchk"
os.makedirs(TMP, exist_ok=True)
def sharp(p):
    a=np.asarray(Image.open(p).convert("L")).astype(np.float32)
    gx=np.diff(a,axis=1); gy=np.diff(a,axis=0)
    return float(gx.var()+gy.var())
TESTS=[("C1905S03.mp4",4.0),("C1905S03.mp4",10.0),("C1899S03.mp4",2.0),("C1898S03.mp4",8.0),
       ("C1866S03.mp4",8.0),("C1879S03.mp4",3.0),("C1895S03.mp4",3.0),("C1894S03.mp4",5.0),
       ("C1825S03.mp4",1.0),("C1846S03.mp4",4.0)]
for f,t in TESTS:
    p=os.path.join(TMP,"%s_%s.png"%(f[:-4],str(t).replace('.','_')))
    r=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1",p],capture_output=True)
    if r.returncode!=0 or not os.path.exists(p):
        print("%-14s t=%5.1f  FAIL"%(f,t)); continue
    print("%-14s t=%5.1f  sharp1080=%8.0f"%(f,t,sharp(p)))
