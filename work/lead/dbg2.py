
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
f, st = "C1828S03.mp4", 0.5
def test(name, extra):
    vf = "trim=start=0:duration=2.0,setpts=PTS-STARTPTS,fps=30,scale=1920:1080:flags=lanczos,setsar=1"
    if extra: vf += ","+extra
    out = os.path.join(WK,"render","dbg2_%s.mp4"%name)
    r = subprocess.run([FF,"-hide_banner","-loglevel","error","-y","-ss","%.3f"%st,"-i",os.path.join(SRC,f),
        "-filter_complex","[0:v]"+vf+"[v]","-map","[v]","-an","-r","30","-frames:v","60",
        "-c:v","libx264","-preset","veryfast","-crf","15","-pix_fmt","yuv420p",out],capture_output=True)
    if r.returncode!=0:
        print("%-40s FAIL %s"%(name, r.stderr.decode("utf-8","replace")[-200:])); return
    p = os.path.join(WK,"render","dbg2_%s.png"%name)
    subprocess.run([FF,"-v","error","-y","-ss","0.5","-i",out,"-frames:v","1",p],check=True)
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    print("%-40s luma=%6.1f std=%5.1f"%(name,Y.mean(),Y.std()))
test("cl_full", "colorlevels=rimin=0.07:rimax=0.96:gimin=0.07:gimax=0.96:bimin=0.07:bimax=0.96")
test("cl_with_out", "colorlevels=rimin=0.07:rimax=0.96:gimin=0.07:gimax=0.96:bimin=0.07:bimax=0.96:romin=0:romax=1:gomin=0:gomax=1:bomin=0:bomax=1")
test("cl_r_only", "colorlevels=rimin=0.07:rimax=0.96")
test("levels_filter", "levels=rimin=0.07:rimax=0.96:gimin=0.07:gimax=0.96:bimin=0.07:bimax=0.96")
