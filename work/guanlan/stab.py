
import os, subprocess, json, numpy as np
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
FILES = ["C1910S03.MP4","C1911S03.MP4","C1912S03.MP4","C1913S03.MP4","C1915S03.MP4","C1916S03.MP4"]
FR=8
def frames(p, w=192, fps=FR):
    cmd=[FF,"-v","error","-i",p,"-vf","fps=%d,scale=%d:-2"%(fps,w),"-f","rawvideo","-pix_fmt","gray","-"]
    r=subprocess.run(cmd,capture_output=True)
    return np.frombuffer(r.stdout,dtype=np.uint8)
res={}
for f in FILES:
    p=os.path.join(SRC,f)
    d=frames(p)
    # frame size unknown; infer by asking ffprobe-ish: use ffmpeg to print? compute w,h from file via scale
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    import re
    m=re.search(r"(\d{3,5})x(\d{3,5})",r); W,H=int(m.group(1)),int(m.group(2))
    h=int(192*H/W/2)*2
    n=len(d)//(192*h)
    fr=d[:n*192*h].reshape(n,h,192).astype(np.float32)
    # per frame: sharpness (variance of laplacian via simple diff), brightness
    lap=np.abs(np.diff(fr,2,axis=1)[:, :, 1:-1] + np.diff(fr,2,axis=2)[:, 1:-1, :])
    sharp=lap.var(axis=(1,2))
    bright=fr.mean(axis=(1,2))
    diff=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2))
    diff=np.concatenate([[0],diff])
    # report per 0.5s
    fps=FR
    step=fps//2
    out=[]
    for i in range(0,n-step,step):
        out.append((round(i/fps,1), round(float(sharp[i:i+step].mean()),1), round(float(bright[i:i+step].mean()),1), round(float(diff[i:i+step].mean()),2)))
    res[f]=dict(n=n,dur=round(n/fps,2),series=out)
print(json.dumps(res))
